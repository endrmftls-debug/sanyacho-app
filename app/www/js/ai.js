// On-device plant recognition with ONNX Runtime Web (WebAssembly). Nothing leaves the phone.
import * as ort from "../lib/ort.wasm.min.mjs";
import { data } from "./data.js";

const st = { status: "idle", progress: 0, error: "", listeners: new Set() };
let session = null;
let loading = null;

export function aiStatus() {
  return st;
}
export function onAIChange(fn) {
  st.listeners.add(fn);
  return () => st.listeners.delete(fn);
}
function emit() {
  for (const fn of st.listeners) {
    try { fn(st); } catch (_) { /* a closed screen */ }
  }
}

export function loadAI() {
  if (loading) return loading;
  loading = (async () => {
    if (!data.labels) {
      st.status = "missing";
      st.error = "AI 모델 정보(labels.json)가 없어요.";
      emit();
      return;
    }
    st.status = "loading";
    emit();
    try {
      ort.env.wasm.wasmPaths = new URL("../lib/", import.meta.url).href;
      const cores = navigator.hardwareConcurrency || 2;
      ort.env.wasm.numThreads = self.crossOriginIsolated ? Math.max(1, Math.min(4, cores - 1)) : 1;
      const res = await fetch("model/plant.onnx");
      if (!res.ok) throw new Error("모델 파일을 찾지 못했어요 (" + res.status + ")");
      const total = Number(res.headers.get("Content-Length")) || 0;
      let buf;
      if (res.body && total) {
        buf = new Uint8Array(total);
        const reader = res.body.getReader();
        let got = 0;
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buf.set(value, got);
          got += value.length;
          st.progress = Math.min(0.95, (got / total) * 0.95);
          emit();
        }
        if (got !== total) buf = buf.slice(0, got);
      } else {
        buf = new Uint8Array(await res.arrayBuffer());
      }
      session = await ort.InferenceSession.create(buf, { executionProviders: ["wasm"], graphOptimizationLevel: "all" });
      st.status = "ready";
      st.progress = 1;
    } catch (e) {
      st.status = "error";
      st.error = String((e && e.message) || e);
    }
    emit();
  })();
  return loading;
}

// Shrink in halves first so a 4000px photo becomes a clean 224px input.
function toInput(src, size) {
  let cur = src;
  let w = src.width;
  let h = src.height;
  const s = Math.min(w, h);
  let sx = (w - s) / 2;
  let sy = (h - s) / 2;
  let side = s;
  while (side > size * 2) {
    const half = Math.round(side / 2);
    const c = document.createElement("canvas");
    c.width = half;
    c.height = half;
    const g = c.getContext("2d");
    g.imageSmoothingEnabled = true;
    g.imageSmoothingQuality = "high";
    g.drawImage(cur, sx, sy, side, side, 0, 0, half, half);
    cur = c;
    sx = 0;
    sy = 0;
    side = half;
  }
  const out = document.createElement("canvas");
  out.width = size;
  out.height = size;
  const g = out.getContext("2d", { willReadFrequently: true });
  g.imageSmoothingEnabled = true;
  g.imageSmoothingQuality = "high";
  g.drawImage(cur, sx, sy, side, side, 0, 0, size, size);
  return g.getImageData(0, 0, size, size).data;
}

export function preprocess(canvas) {
  const { size, mean, std } = data.labels.input;
  const px = toInput(canvas, size);
  const n = size * size;
  const x = new Float32Array(3 * n);
  for (let i = 0; i < n; i++) {
    x[i] = (px[i * 4] / 255 - mean[0]) / std[0];
    x[n + i] = (px[i * 4 + 1] / 255 - mean[1]) / std[1];
    x[2 * n + i] = (px[i * 4 + 2] / 255 - mean[2]) / std[2];
  }
  return x;
}

function softmax(logits) {
  let m = -Infinity;
  for (const v of logits) m = Math.max(m, v);
  const e = Array.from(logits, (v) => Math.exp(v - m));
  const s = e.reduce((a, b) => a + b, 0);
  return e.map((v) => v / s);
}

// Average the probabilities of every photo (whole plant, leaf front/back, flower...).
export async function classify(canvases) {
  if (!session) throw new Error("AI가 아직 준비되지 않았어요.");
  const { size } = data.labels.input;
  const C = data.labels.classes.length;
  const sum = new Float64Array(C);
  for (const cv of canvases) {
    const t = new ort.Tensor("float32", preprocess(cv), [1, 3, size, size]);
    const out = await session.run({ pixel_values: t });
    const p = softmax(out.logits.data);
    for (let i = 0; i < C; i++) sum[i] += p[i];
  }
  return Array.from(sum, (v) => v / canvases.length);
}

const DANGER = new Set(["toxic", "deadly"]);
const EDIBLE = new Set(["edible", "edible_caution"]);
// Stricter than the training default (0.75): on validation photos 0.85 halves toxic-shown-as-edible (0.48% -> 0.24%).
const MIN_CONFIDENT = 0.85;
const MIN_DANGER = 0.4;

// Turn probabilities into one safety verdict for the result screen.
export function decide(probs) {
  const cls = data.labels.classes;
  const th = data.labels.thresholds;
  const ranked = probs.map((p, i) => ({ p, c: cls[i] })).sort((a, b) => b.p - a.p);
  const top = ranked[0];
  let mush = 0;
  let tox = 0;
  for (const r of ranked) {
    if (r.c.group === "mushroom" || r.c.id === "other_fungi") mush += r.p;
    if (DANGER.has(r.c.category)) tox += r.p;
  }
  const topToxic = ranked.find((r) => DANGER.has(r.c.category));
  const base = { ranked, top, mush, tox, topToxic, warn: tox >= th.toxic_warn && !DANGER.has(top.c.category) };
  if (mush >= 0.5) return { ...base, kind: "mushroom" };
  // Saying "this may be poisonous" needs less certainty than saying "this may be edible".
  if (DANGER.has(top.c.category) && top.p >= MIN_DANGER) return { ...base, kind: top.c.category === "deadly" ? "deadly" : "toxic" };
  if (top.c.id === "other_plant" || top.p < Math.max(th.confident, MIN_CONFIDENT)) return { ...base, kind: "unsure" };
  if (top.c.category === "inedible") return { ...base, kind: "inedible" };
  if (EDIBLE.has(top.c.category)) return { ...base, kind: "edible" };
  return { ...base, kind: "unsure" };
}
