// All screens. Each returns an optional cleanup function (stop camera, GPS, sound...).
import { $, $$, esc, josa, pct, VERDICT, verdictOf, badge, toast, fmtDate, keepScreenOn } from "./util.js";
import { data, entry, photos, firstPhoto, inSeason, aiKnows } from "./data.js";
import { aiStatus, onAIChange, loadAI, classify, decide } from "./ai.js";
import { addFind, listFinds, getFind, deleteFind } from "./store.js";
import { getPosition, watchPosition, posErrorText, dms, distanceM, bearingDeg, direction, fmtDistance } from "./geo.js";
import { startWhistle, stopWhistle, whistleOn } from "./sound.js";

export const app = { shots: [], result: null, unlocked: new Set() };
const MAX_SHOTS = 4;
const SHOT_TIPS = ["식물 전체 모습", "잎 앞면을 가까이", "잎 뒷면이나 줄기", "꽃·열매·뿌리 (있으면)"];

const nameOf = (id) => entry(id)?.ko || data.labels?.classes.find((c) => c.id === id)?.ko || id;

function vcls(category, group) {
  if (group === "mushroom" || (category || "").startsWith("mushroom")) return "fungus";
  return { edible: "safe", edible_caution: "caution", toxic: "danger", deadly: "deadly", inedible: "unknown" }[category] || "unknown";
}

/* ---------------- 확인 (home) ---------------- */
export function home(view) {
  const m = new Date().getMonth() + 1;
  const list = inSeason(m).slice(0, 14);
  view.innerHTML = `
    <section class="home">
      <button class="viewfinder" data-go="#camera"><span class="c3"></span><span class="c4"></span>
        <span><b>카메라로 확인하기</b><small>잎·줄기·꽃을 여러 장 찍으면 더 정확해요</small></span></button>
      <div class="btn-row" style="grid-template-columns:1fr">
        <label class="btn ghost">갤러리 사진으로 확인<input type="file" accept="image/*" multiple hidden id="pick"></label>
      </div>
      <h2>${m}월, 지금 산에서 구할 수 있는 것</h2>
      ${list.length ? `<div class="tiles">${list.map((e) => {
        const ph = firstPhoto(e.id);
        return `<a class="tile" href="#sp/${e.id}"><div class="ph">${ph ? `<img src="${ph}" alt="" loading="lazy">` : "사진 없음"}</div>
          <b>${esc(e.ko)}</b><span>${esc(e.eat?.part || "")}</span></a>`;
      }).join("")}</div>` : `<p class="muted">이번 달에 먹을 수 있는 것으로 정리된 식물이 없어요.</p>`}
      <p class="note">확실하지 않으면 먹지 마세요. 버섯은 먹지 마세요.</p>
      <div id="aistatus" class="status"></div>
    </section>`;
  $("[data-go]", view).onclick = () => { clearShots(); location.hash = "#camera"; };
  $("#pick", view).onchange = async (ev) => {
    await addFiles(ev.target.files, true);
    if (app.shots.length) location.hash = "#result";
  };
  const box = $("#aistatus", view);
  const paint = (s) => {
    box.classList.toggle("err", s.status === "error" || s.status === "missing");
    if (s.status === "ready") {
      const n = data.labels.classes.length;
      const prov = data.labels.classes.filter((c) => c.provisional).length;
      box.textContent = `AI 준비 완료: ${n}종류를 알아봐요${prov ? `(그중 ${prov}종류는 참고용)` : ""}. 인터넷 없이 동작해요.`;
    }
    else if (s.status === "loading") box.innerHTML = `AI 준비 중… ${Math.round(s.progress * 100)}%<div class="meter" style="--p:${s.progress}"><i></i></div>`;
    else if (s.status === "error" || s.status === "missing") box.textContent = `AI를 불러오지 못했어요: ${s.error} 도감은 그대로 쓸 수 있어요.`;
    else box.textContent = "AI 준비 전";
  };
  paint(aiStatus());
  return onAIChange(paint);
}

/* ---------------- camera ---------------- */
async function fileToCanvas(file) {
  const bmp = await createImageBitmap(file);
  const s = Math.min(bmp.width, bmp.height);
  const side = Math.min(1024, s);
  const c = document.createElement("canvas");
  c.width = side;
  c.height = side;
  const g = c.getContext("2d");
  g.imageSmoothingQuality = "high";
  g.drawImage(bmp, (bmp.width - s) / 2, (bmp.height - s) / 2, s, s, 0, 0, side, side);
  bmp.close && bmp.close();
  return c;
}

async function addCanvas(c) {
  const blob = await new Promise((r) => c.toBlob(r, "image/jpeg", 0.85));
  app.shots.push({ canvas: c, blob, url: URL.createObjectURL(blob) });
}

async function addFiles(files, reset) {
  if (reset) clearShots();
  for (const f of Array.from(files || []).slice(0, MAX_SHOTS - app.shots.length)) {
    try { await addCanvas(await fileToCanvas(f)); } catch (_) { toast("사진을 열지 못했어요."); }
  }
}

export function clearShots() {
  for (const s of app.shots) URL.revokeObjectURL(s.url);
  app.shots = [];
  app.result = null;
}

export function camera(view) {
  view.innerHTML = `
    <section class="cam">
      <div class="viewport"><video playsinline muted autoplay></video><div class="guide"></div>
        <div class="step" id="step"></div>
        <div class="camerr" id="camerr" hidden><div><p id="camerrmsg"></p>
          <button class="btn" id="camretry">카메라 다시 켜기</button>
          <button class="btn ghost" id="camsettings" hidden style="margin-top:8px">권한 설정 열기</button>
          <p class="small" id="camerrdetail" style="margin-top:10px;opacity:.75"></p></div></div></div>
      <p class="tip" id="tip"></p>
      <div class="shots" id="shots"></div>
      <div class="camctl">
        <button class="btn ghost side" id="torch" hidden>불 켜기</button><span id="torchgap"></span>
        <button class="shutter" id="shutter" aria-label="찍기"></button>
        <button class="btn side" id="analyze" disabled>분석</button>
      </div>
      <label class="linkbtn" style="display:block;text-align:center">갤러리에서 고르기<input type="file" accept="image/*" multiple hidden id="gal"></label>
    </section>`;
  const video = $("video", view);
  let stream = null;
  let starting = false;
  let alive = true; // false once the user leaves this screen
  let torchOn = false;
  keepScreenOn(true);

  const paint = () => {
    const n = app.shots.length;
    $("#step", view).textContent = n < MAX_SHOTS ? `${n + 1}/${MAX_SHOTS}  ${SHOT_TIPS[n]}` : "4장 모두 찍었어요";
    $("#tip", view).textContent = n === 0 ? "식물이 네모 안에 꽉 차게 찍어 주세요." :
      n < MAX_SHOTS ? `다음: ${SHOT_TIPS[n]}. 한 장만으로도 분석할 수 있어요.` : "분석을 눌러 주세요.";
    $("#shots", view).innerHTML = Array.from({ length: MAX_SHOTS }, (_, i) => {
      const s = app.shots[i];
      return s ? `<div class="shot"><img src="${s.url}" alt="${i + 1}번째 사진"><button data-del="${i}" aria-label="${i + 1}번째 사진 지우기">×</button></div>`
        : `<div class="shot">${SHOT_TIPS[i]}</div>`;
    }).join("");
    $$("[data-del]", view).forEach((b) => (b.onclick = () => {
      const [s] = app.shots.splice(Number(b.dataset.del), 1);
      URL.revokeObjectURL(s.url);
      paint();
    }));
    $("#analyze", view).disabled = n === 0;
    $("#analyze", view).textContent = n ? `분석 ${n}장` : "분석";
    $("#shutter", view).disabled = n >= MAX_SHOTS;
  };
  paint();

  const stopStream = () => {
    if (stream) stream.getTracks().forEach((t) => t.stop());
    stream = null;
    video.srcObject = null;
  };
  const isLive = () => !!stream && stream.getVideoTracks().some((t) => t.readyState === "live");

  const showError = (e) => {
    const name = (e && e.name) || "";
    let msg = "카메라를 켜지 못했어요.";
    if (name === "NotAllowedError" || name === "SecurityError") {
      msg = "카메라 권한이 꺼져 있어요. '권한 설정 열기'에서 카메라를 허용한 뒤 '카메라 다시 켜기'를 눌러 주세요.";
    } else if (name === "NotReadableError" || name === "AbortError" || name === "TrackStartError") {
      msg = "다른 앱이 카메라를 쓰고 있거나, 빠른 설정의 '카메라 액세스'가 꺼져 있을 수 있어요. 확인한 뒤 '카메라 다시 켜기'를 눌러 주세요.";
    } else if (name === "NotFoundError" || name === "OverconstrainedError") {
      msg = "카메라를 찾지 못했어요.";
    }
    $("#camerrmsg", view).textContent = msg + " 아래 '갤러리에서 고르기'로 사진을 골라도 돼요.";
    $("#camerrdetail", view).textContent = e ? `오류: ${name || "알 수 없음"} ${e.message || ""}`.trim() : "";
    const settings = $("#camsettings", view);
    const bridge = window.AndroidApp && typeof window.AndroidApp.openAppSettings === "function";
    settings.hidden = !(bridge && (name === "NotAllowedError" || name === "SecurityError"));
    $("#camerr", view).hidden = false;
  };

  const setupTorch = (track) => {
    const caps = track.getCapabilities ? track.getCapabilities() : {};
    const t = $("#torch", view);
    if (!caps.torch || !t) return;
    t.hidden = false;
    $("#torchgap", view)?.remove();
    torchOn = false;
    t.textContent = "불 켜기";
    t.onclick = async () => {
      torchOn = !torchOn;
      try { await track.applyConstraints({ advanced: [{ torch: torchOn }] }); } catch (_) { torchOn = false; }
      t.textContent = torchOn ? "불 끄기" : "불 켜기";
    };
  };

  // Ask for the back camera; fall back to simpler requests if a phone refuses the first one.
  const start = async () => {
    if (!alive || starting || isLive()) return;
    starting = true;
    $("#camerr", view).hidden = true;
    const tries = [
      { video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1440 } }, audio: false },
      { video: { facingMode: { ideal: "environment" } }, audio: false },
      { video: true, audio: false },
    ];
    let last = null;
    for (const c of tries) {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw Object.assign(new Error("이 화면에서는 카메라를 쓸 수 없어요"), { name: "NotSupportedError" });
        }
        const s = await navigator.mediaDevices.getUserMedia(c);
        if (!alive) { s.getTracks().forEach((t) => t.stop()); starting = false; return; } // user already left
        stopStream();
        stream = s;
        video.srcObject = s;
        try { await video.play(); } catch (_) { /* autoplay is allowed in the app */ }
        const track = s.getVideoTracks()[0];
        track.addEventListener("ended", () => { if (alive && stream === s) stream = null; });
        setupTorch(track);
        starting = false;
        return;
      } catch (e) {
        last = e;
        if (e && (e.name === "NotAllowedError" || e.name === "SecurityError" || e.name === "NotSupportedError")) break;
      }
    }
    starting = false;
    if (alive) showError(last);
  };

  // Android takes the camera away while another screen (permission box, gallery) is on top; turn it back on after.
  const onVisible = () => { if (document.visibilityState === "visible") start(); };
  document.addEventListener("visibilitychange", onVisible);
  window.appResume = () => start();
  $("#camretry", view).onclick = () => { stopStream(); start(); };
  $("#camsettings", view).onclick = () => { try { window.AndroidApp.openAppSettings(); } catch (_) { /* not in the app */ } };
  start();

  $("#shutter", view).onclick = async () => {
    if (app.shots.length >= MAX_SHOTS) return;
    if (!isLive() || !video.videoWidth) {
      toast("카메라가 아직 켜지지 않았어요.");
      start();
      return;
    }
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    const s = Math.min(vw, vh);
    const side = Math.min(1024, s);
    const c = document.createElement("canvas");
    c.width = side;
    c.height = side;
    c.getContext("2d").drawImage(video, (vw - s) / 2, (vh - s) / 2, s, s, 0, 0, side, side);
    await addCanvas(c);
    paint();
  };
  $("#gal", view).onchange = async (ev) => { await addFiles(ev.target.files, false); if (alive) paint(); };
  $("#analyze", view).onclick = () => { app.result = null; location.hash = "#result"; };

  return () => {
    alive = false;
    document.removeEventListener("visibilitychange", onVisible);
    if (window.appResume) window.appResume = null;
    keepScreenOn(false);
    stopStream();
  };
}

/* ---------------- result ---------------- */
function provNote(d) {
  if (!d.provisional) return "";
  const n = d.top.c.photos;
  const name = nameOf(d.top.c.id);
  const why = `AI 참고용: ${esc(name)}${josa(name, "은", "는")} ${n ? `사진 ${n}장으로만` : "적은 사진으로"} 배운 종류라 틀릴 수 있어요.`;
  return `<p class="prov">${why}${d.kind === "deadly" || d.kind === "toxic" ? " 그래도 독초일 수 있으니 먹지 마세요." : ""}</p>`;
}

function signHTML(d) {
  return signCore(d).replace(/<\/div>$/, `${provNote(d)}</div>`);
}

function signCore(d) {
  const t = d.top;
  const name = esc(nameOf(t.c.id));
  const sub = (s) => `<p class="sub">${s}</p>`;
  switch (d.kind) {
    case "mushroom": {
      const best = d.ranked.find((r) => r.c.group === "mushroom");
      return `<div class="sign fungus"><p class="kicker">버섯이에요</p><h1>먹지 마세요</h1>
        ${best ? sub(`가장 비슷한 버섯: ${esc(nameOf(best.c.id))} ${pct(best.p)}`) : ""}</div>`;
    }
    case "unsure":
      return `<div class="sign unknown"><p class="kicker">확실하지 않아요</p><h1>먹지 마세요</h1>
        ${t.c.id !== "other_plant" ? sub(`가장 가까운 후보: ${name} ${pct(t.p)}`) : sub("도감에 없는 식물일 수 있어요")}</div>`;
    case "deadly":
      return `<div class="sign deadly"><p class="kicker">맹독 식물일 수 있어요</p><h1>${name}</h1>${sub(`AI 판단 ${pct(t.p)}`)}</div>`;
    case "toxic":
      return `<div class="sign danger"><p class="kicker">독초일 수 있어요</p><h1>${name}</h1>${sub(`AI 판단 ${pct(t.p)}`)}</div>`;
    case "inedible":
      return `<div class="sign unknown"><p class="kicker">먹지 않는 식물</p><h1>${name}</h1>${sub(`AI 판단 ${pct(t.p)}`)}</div>`;
    default:
      return `<div class="sign safe"><p class="kicker">먹을 수 있는 식물 후보</p><h1>${name}</h1>${sub(`AI 판단 ${pct(t.p)}`)}
        <p class="hold">아직 먹지 마세요. 닮은 독초와 구별하는 체크리스트를 먼저 확인해야 먹는 법이 열려요.</p></div>`;
  }
}

function adviceHTML(d) {
  const top = d.top.c.id;
  switch (d.kind) {
    case "mushroom":
      return `<p>버섯은 사진으로 먹을 수 있는지 알 수 없어요. 독버섯 가운데에는 조금만 먹어도 목숨을 잃는 것이 있어요.</p>`;
    case "unsure":
      if (d.provisional) {
        return `<p>AI가 덜 배운 종류라 사진만으로는 판단하지 않아요. 도감의 사진·생김새·닮은 독초와 직접 비교해 보세요.</p>
          <a class="btn ghost" href="#sp/${top}">${esc(nameOf(top))} 도감에서 비교하기</a>`;
      }
      return `<p>잎 뒷면, 줄기, 꽃이나 열매를 더 찍어 보세요. 그래도 모르겠으면 먹지 않는 것이 안전해요.</p>`;
    case "deadly":
    case "toxic":
      return `<p>먹지 마세요. 이미 먹었다면 바로 119에 연락하고 남은 식물을 챙기세요. <a href="#guide/aid">응급처치 보기</a></p>`;
    case "inedible":
      return `<p>먹지 않는 식물이에요. <a href="#sp/${top}">자세히 보기</a></p>`;
    default:
      return `<a class="btn" href="#sp/${top}?from=result">확인하고 먹는 법 보기</a>`;
  }
}

export function result(view) {
  if (!app.shots.length) {
    view.innerHTML = `<p class="empty">분석할 사진이 없어요.</p><a class="btn" href="#camera">카메라로 찍기</a>`;
    return;
  }
  const st = aiStatus();
  const thumbs = `<div class="thumbs">${app.shots.map((s, i) => `<img src="${s.url}" alt="${i + 1}번째 사진">`).join("")}</div>`;
  const render = () => {
    const d = app.result;
    const cands = d.ranked.slice(0, 5).filter((r, i) => i === 0 || r.p >= 0.01);
    view.innerHTML = `
      <section class="result">
        ${signHTML(d)}
        ${d.warn && d.topToxic ? `<p class="alert">독초 ${esc(nameOf(d.topToxic.c.id))}일 가능성도 ${pct(d.topToxic.p)} 있어요. 닮은 독초 구별 포인트를 꼭 확인하세요.</p>` : ""}
        ${adviceHTML(d)}
        <h2>후보</h2>
        <ol class="cands">${cands.map((r) => {
          const vc = vcls(r.c.category, r.c.group);
          const lab = r.c.group === "mushroom" ? "버섯" : (VERDICT[entry(r.c.id)?.v]?.label || "");
          return `<li><a href="#sp/${r.c.id}" style="--c:var(--${vc === "fungus" ? "fungus" : vc})">
            <span class="n">${esc(nameOf(r.c.id))}${lab ? ` <span class="badge ${vc}">${esc(lab)}</span>` : ""}${r.c.provisional ? ` <span class="tag-prov">AI 참고용</span>` : ""}</span>
            <span class="p">${pct(r.p)}</span><span class="b" style="--p:${r.p.toFixed(3)}"><i></i></span></a></li>`;
        }).join("")}</ol>
        <p class="small muted" style="margin-top:8px">${app.shots.length === 1 ? "사진 1장으로 판단했어요. 잎 뒷면·줄기·꽃을 더 찍으면 더 정확해요." : `사진 ${app.shots.length}장을 함께 판단했어요.`}</p>
        ${thumbs}
        <div class="btn-row">
          <a class="btn ghost" href="#camera">다른 각도로 더 찍기</a>
          <button class="btn ghost" id="save">일지에 저장</button>
        </div>
      </section>`;
    $("#save", view).onclick = () => saveFind(d);
  };
  if (app.result) { render(); return; }
  if (st.status !== "ready") {
    view.innerHTML = `<div class="spinner"></div><p class="empty" id="wait">AI 준비 중이에요…</p>${thumbs}`;
    if (st.status === "error" || st.status === "missing") {
      view.innerHTML = `<p class="alert">AI를 불러오지 못했어요: ${esc(st.error)}</p><p>도감에서 직접 찾아보세요.</p><a class="btn" href="#book">도감 열기</a>`;
      return;
    }
    loadAI();
    return onAIChange((s) => { if (s.status === "ready" || s.status === "error") result(view); });
  }
  view.innerHTML = `<div class="spinner"></div><p class="empty">분석 중이에요… (사진 ${app.shots.length}장)</p>${thumbs}`;
  setTimeout(async () => {
    try {
      const probs = await classify(app.shots.map((s) => s.canvas));
      app.result = decide(probs);
      render();
    } catch (e) {
      view.innerHTML = `<p class="alert">분석하지 못했어요: ${esc(e.message || e)}</p><a class="btn" href="#camera">다시 찍기</a>`;
    }
  }, 60);
}

async function saveFind(d) {
  const btn = document.getElementById("save");
  if (btn) { btn.disabled = true; btn.textContent = "위치 찾는 중…"; }
  let pos = null;
  try { pos = await getPosition(15000); } catch (_) { /* save without a position */ }
  const t = d.top;
  await addFind({
    classId: t.c.id, name: nameOf(t.c.id), prob: t.p, kind: d.kind,
    lat: pos?.coords.latitude, lon: pos?.coords.longitude, acc: pos?.coords.accuracy, alt: pos?.coords.altitude,
    photo: app.shots[0]?.blob || null,
  });
  if (btn) btn.textContent = "저장했어요";
  toast(pos ? "일지에 저장했어요." : "일지에 저장했어요. 위치는 찾지 못했어요.");
}

/* ---------------- species page ---------------- */
function aiLine(e) {
  switch (aiKnows(e)) {
    case "provisional":
      return `<span class="tag-prov">AI 참고용</span><span class="small muted">사진 ${e.aiPhotos || "몇"}장으로만 배워서 카메라 결과는 참고만 하세요</span>`;
    case "learned":
      return typeof e.aiAcc === "number" ? `<span class="small muted">AI 시험 정답률 ${Math.round(e.aiAcc * 100)}%</span>` : "";
    case "unknown":
      return `<span class="small muted">아직 AI가 사진으로 알아보지 못하는 종류예요</span>`;
    default:
      return "";
  }
}
function listHTML(items) {
  return `<ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
}

export function species(view, id, query) {
  const e = entry(id);
  if (!e) {
    view.innerHTML = `<p class="empty">도감에 없는 항목이에요.</p>`;
    return;
  }
  const v = verdictOf(e);
  const pics = photos(id);
  const edible = e.v === "edible" || e.v === "edible_caution";
  const twins = [...(e.like || []), ...(e.like_auto || [])];
  const fromResult = query.get("from") === "result" && app.result && app.result.top.c.id === id;
  const months = (e.months || []).length ? `${e.months.join(", ")}월` : "";
  // entries that cover several species label each photo; say which species have no photo
  const named = new Set(pics.map((p) => p.name).filter(Boolean));
  const noPhoto = named.size ? (e.aka || []).filter((a) => !named.has(a)) : [];
  view.innerHTML = `
    <article>
      ${pics.length ? `<div class="photos">${pics.map((p) => `<figure><img src="${p.src}" alt="${esc(p.name || e.ko)} 사진" loading="lazy">
        <figcaption>${p.name ? `<b>${esc(p.name)}</b><br>` : ""}${esc(p.credit)}</figcaption></figure>`).join("")}</div>` : ""}
      ${noPhoto.length ? `<p class="pnote">${esc(noPhoto.join(", "))}${josa(noPhoto[noPhoto.length - 1], "은", "는")} 자유롭게 쓸 수 있는 사진이 없어 싣지 못했어요. 아래 생김새 설명으로 확인하세요.</p>` : ""}
      <header class="sp-head">
        <h1>${esc(e.ko)}</h1>
        ${e.aka?.length ? `<p class="aka">다른 이름: ${esc(e.aka.join(", "))}</p>` : ""}
        <p class="sci">${esc(e.sci)}${e.fam ? `<span class="muted" style="font-style:normal">, ${esc(e.fam)}</span>` : ""}</p>
        <div class="meta">${badge(e)}
          ${fromResult ? `<span class="small">AI 판단 ${pct(app.result.top.p)}</span>` : ""}
          ${aiLine(e)}</div>
      </header>
      <p class="lead">${esc(e.sum)}</p>
      ${twins.length ? `<h2>닮은 식물과 구별하기</h2><div class="twins">${twins.map(([tid, why]) => {
        const t = entry(tid);
        const dangerous = t && (t.v === "toxic" || t.v === "deadly" || t.v === "mushroom");
        return `<a class="twin ${dangerous ? "" : "mild"}" href="#sp/${tid}"><b>${esc(t?.ko || tid)} ${t ? badge(t) : ""}</b>${esc(why)}</a>`;
      }).join("")}</div>` : ""}
      ${e.look?.length ? `<h2>생김새</h2>${listHTML(e.look)}` : ""}
      <dl class="facts">
        ${e.where ? `<dt>자라는 곳</dt><dd>${esc(e.where)}</dd>` : ""}
        ${months && edible ? `<dt>먹을 수 있는 때</dt><dd>${esc(months)}</dd>` : ""}
        ${e.energy && edible ? `<dt>열량</dt><dd>${esc(e.energy)}</dd>` : ""}
      </dl>
      ${e.tox ? `<h2>독성</h2><div class="tox"><p><b>독이 있는 부위:</b> ${esc(e.tox.part)}</p><p style="margin:0">${esc(e.tox.sym)}</p>
        ${e.v === "inedible" ? "" : `<p style="margin:10px 0 0"><a href="#guide/aid">먹었다면: 응급처치 보기</a></p>`}</div>` : ""}
      ${edible ? `<h2>먹는 법</h2><div id="eat"></div>` : ""}
      ${e.surv ? `<h2>생존 활용</h2><p>${esc(e.surv)}</p>` : ""}
      ${e.med ? `<h2>약초로서</h2><p class="medic">${esc(e.med)}</p>` : ""}
      ${e.warn?.length ? `<h2>주의</h2><ul class="warnlist">${e.warn.map((w) => `<li>${esc(w)}</li>`).join("")}</ul>` : ""}
    </article>`;
  if (edible) paintEat($("#eat", view), e);
}

function paintEat(box, e) {
  if (!app.unlocked.has(e.id)) {
    box.innerHTML = `<div class="lockbox"><h3>먼저 실제 식물로 확인해 주세요</h3>
      <p class="small muted">모두 맞을 때만 먹는 법이 열려요. 하나라도 아니면 먹지 마세요.</p>
      ${e.check.map((c, i) => `<label class="check"><input type="checkbox" data-i="${i}"><span>${esc(c)}</span></label>`).join("")}
      <button class="btn" id="unlock" disabled>모두 확인했어요</button></div>`;
    const boxes = $$("input[type=checkbox]", box);
    const btn = $("#unlock", box);
    boxes.forEach((b) => (b.onchange = () => (btn.disabled = !boxes.every((x) => x.checked))));
    btn.onclick = () => { app.unlocked.add(e.id); paintEat(box, e); };
    return;
  }
  const eat = e.eat || {};
  box.innerHTML = `<div class="eat">
      <p><b>먹는 부위:</b> ${esc(eat.part || "")}</p>
      ${eat.how?.length ? `<h3>손질</h3><ol>${eat.how.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>` : ""}
      ${(eat.recipes || []).map(([n, how]) => `<div class="recipe"><b>${esc(n)}</b><p style="margin:4px 0 0">${esc(how)}</p></div>`).join("")}
      <p class="small muted" style="margin-top:12px">처음 먹는 것은 조금만 드세요.</p></div>`;
}

/* ---------------- 도감 ---------------- */
const FILTERS = [
  ["all", "전체"], ["food", "먹을 수 있음"], ["danger", "독초"], ["fungus", "버섯"], ["season", "이번 달"], ["ai", "AI 참고용"],
];
let bookState = { q: "", f: "all" };

export function book(view) {
  view.innerHTML = `
    <input class="search" type="search" placeholder="이름으로 찾기 (예: 곰취, 명이)" value="${esc(bookState.q)}" aria-label="이름으로 찾기">
    <div class="chips">${FILTERS.map(([k, l]) => `<button class="chip" data-f="${k}" aria-pressed="${bookState.f === k}">${l}</button>`).join("")}</div>
    <ul class="rows" id="rows"></ul>`;
  const m = new Date().getMonth() + 1;
  const paint = () => {
    const q = bookState.q.trim().toLowerCase();
    const rows = data.species.filter((e) => {
      if (e.id === "other_plant" || e.id === "other_fungi") return false;
      if (bookState.f === "food" && !(e.v === "edible" || e.v === "edible_caution")) return false;
      if (bookState.f === "danger" && !(e.v === "toxic" || e.v === "deadly" || e.v === "inedible")) return false;
      if (bookState.f === "fungus" && e.v !== "mushroom") return false;
      if (bookState.f === "season" && !((e.v === "edible" || e.v === "edible_caution") && (e.months || []).includes(m))) return false;
      if (bookState.f === "ai" && !["provisional", "unknown"].includes(aiKnows(e))) return false;
      if (!q) return true;
      return [e.ko, ...(e.aka || []), e.sci].join(" ").toLowerCase().includes(q);
    }).sort((a, b) => a.ko.localeCompare(b.ko, "ko"));
    $("#rows", view).innerHTML = rows.length ? rows.map((e) => {
      const v = verdictOf(e);
      const ph = firstPhoto(e.id);
      const ai = aiKnows(e);
      const line = bookState.f === "ai"
        ? (ai === "provisional" ? `사진 ${e.aiPhotos || "몇"}장으로만 배웠어요. 카메라 결과는 참고만 하세요.` : "카메라 AI가 아직 알아보지 못해요. 도감으로 확인하세요.")
        : (e.sum.length > 46 ? e.sum.slice(0, 45) + "…" : e.sum);
      return `<li><a class="c-${v.cls}" href="#sp/${e.id}">${ph ? `<img class="th" src="${ph}" alt="" loading="lazy">` : `<span class="th"></span>`}
        <span><b>${esc(e.ko)}${ai === "provisional" ? ` <span class="tag-prov">AI 참고용</span>` : ""}</b><small>${esc(line)}</small></span>
        <span class="right">${esc(v.label.replace(": 먹지 마세요", ""))}</span></a></li>`;
    }).join("") : `<li class="empty">${bookState.f === "ai" && !q ? (data.labels ? "AI가 도감의 모든 종류를 배웠어요." : "AI 모델이 없어서 확인할 수 없어요.") : "찾는 식물이 없어요."}</li>`;
  };
  paint();
  $(".search", view).oninput = (ev) => { bookState.q = ev.target.value; paint(); };
  $$(".chip", view).forEach((c) => (c.onclick = () => {
    bookState.f = c.dataset.f;
    $$(".chip", view).forEach((x) => x.setAttribute("aria-pressed", String(x === c)));
    paint();
  }));
}

/* ---------------- 일지 ---------------- */
export function journal(view) {
  view.innerHTML = `
    <form class="pinform" id="pin"><input name="note" placeholder="지금 위치에 메모 (예: 두릅 군락)" aria-label="메모">
      <button class="btn" type="submit">위치 저장</button></form>
    <p class="small muted" id="here">현재 위치 찾는 중…</p>
    <ul class="rows" id="finds"></ul>`;
  let here = null;
  let finds = [];
  const paint = () => {
    $("#finds", view).innerHTML = finds.length ? finds.map((f) => {
      const e = entry(f.classId);
      const v = e ? verdictOf(e) : VERDICT.other;
      let rel = "";
      if (here && f.lat != null) {
        const p = { lat: f.lat, lon: f.lon };
        rel = `${direction(bearingDeg(here, p))}쪽 ${fmtDistance(distanceM(here, p))}`;
      }
      return `<li><a class="c-${f.classId ? v.cls : "unknown"}" href="#find/${f.id}">
        ${f.photo ? `<img class="th" data-photo="${f.id}" alt="">` : `<span class="th"></span>`}
        <span><b>${esc(f.name || f.note || "위치 메모")}</b><small>${fmtDate(f.time)}${f.note && f.name ? "<br>" + esc(f.note) : ""}</small></span>
        <span class="right">${esc(rel)}</span></a></li>`;
    }).join("") : `<li class="empty">아직 저장한 기록이 없어요. 사진 분석 결과에서 '일지에 저장'을 누르거나, 위에서 지금 위치를 저장하세요.</li>`;
    for (const f of finds) {
      const img = view.querySelector(`[data-photo="${f.id}"]`);
      if (img && f.photo) img.src = URL.createObjectURL(f.photo);
    }
  };
  listFinds().then((r) => { finds = r; paint(); });
  const stop = watchPosition((p) => {
    here = { lat: p.coords.latitude, lon: p.coords.longitude };
    $("#here", view).textContent = `현재 위치 정확도 약 ${Math.round(p.coords.accuracy)}m. 거리와 방향은 여기서부터예요.`;
    paint();
  }, (err) => { $("#here", view).textContent = posErrorText(err); });
  $("#pin", view).onsubmit = async (ev) => {
    ev.preventDefault();
    const note = ev.target.note.value.trim();
    const btn = $("button", ev.target);
    btn.disabled = true;
    try {
      const p = await getPosition(20000);
      await addFind({ note: note || "위치 메모", lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy, alt: p.coords.altitude });
      ev.target.reset();
      finds = await listFinds();
      paint();
      toast("지금 위치를 저장했어요.");
    } catch (err) {
      toast(posErrorText(err) || "위치를 찾지 못했어요.");
    }
    btn.disabled = false;
  };
  return stop;
}

export function find(view, id) {
  let armed = false;
  getFind(id).then((f) => {
    if (!f) { view.innerHTML = `<p class="empty">기록을 찾지 못했어요.</p>`; return; }
    const e = f.classId ? entry(f.classId) : null;
    view.innerHTML = `
      ${f.photo ? `<img id="ph" alt="저장한 사진" style="width:100%;border-radius:14px;margin-bottom:14px">` : ""}
      <h1 style="font:400 30px/1.2 var(--sign)">${esc(f.name || f.note || "위치 메모")}</h1>
      <p class="muted">${fmtDate(f.time)}</p>
      ${e ? `<p>${badge(e)} ${f.prob != null ? `<span class="small">AI 판단 ${pct(f.prob)}</span>` : ""}</p><a class="btn ghost" href="#sp/${e.id}">도감에서 보기</a>` : ""}
      ${f.note && f.name ? `<p style="margin-top:12px">${esc(f.note)}</p>` : ""}
      ${f.lat != null ? `<div class="plate" style="margin-top:16px"><p class="lab">저장한 위치</p>
        <p class="big" style="font-size:30px">${f.lat.toFixed(5)}, ${f.lon.toFixed(5)}</p>
        <p class="dms">${dms(f.lat, "N", "S")} ${dms(f.lon, "E", "W")}</p>
        <p class="acc">정확도 약 ${Math.round(f.acc || 0)}m${f.alt != null ? `, 고도 ${Math.round(f.alt)}m` : ""}</p></div>
        <p id="rel" class="muted" style="margin-top:10px"></p>` : `<p class="muted">위치 없이 저장된 기록이에요.</p>`}
      <button class="btn warn" id="del" style="margin-top:20px">기록 삭제</button>`;
    if (f.photo) $("#ph", view).src = URL.createObjectURL(f.photo);
    $("#del", view).onclick = async (ev) => {
      if (!armed) { armed = true; ev.target.textContent = "한 번 더 누르면 삭제돼요"; return; }
      await deleteFind(id);
      toast("기록을 삭제했어요.");
      history.back();
    };
    if (f.lat != null) {
      getPosition(15000).then((p) => {
        const here = { lat: p.coords.latitude, lon: p.coords.longitude };
        const to = { lat: f.lat, lon: f.lon };
        const el = $("#rel", view);
        if (el) el.textContent = `지금 위치에서 ${direction(bearingDeg(here, to))}쪽으로 ${fmtDistance(distanceM(here, to))}`;
      }).catch(() => {});
    }
  });
}

/* ---------------- 가이드 ---------------- */
function itemHTML(it) {
  if (it.t === "h") return `<h3>${esc(it.v)}</h3>`;
  if (it.t === "ul") return listHTML(it.v);
  return `<p>${esc(it.v)}</p>`;
}

export function guide(view, openId) {
  view.innerHTML = `<section class="guide">${data.guide.map((g) => `
    <details id="g-${g.id}" ${g.id === openId ? "open" : ""}><summary><span aria-hidden="true">${g.icon}</span>${esc(g.title)}</summary>
      <div class="body">${g.items.map(itemHTML).join("")}</div></details>`).join("")}</section>`;
  if (openId) setTimeout(() => document.getElementById("g-" + openId)?.scrollIntoView({ block: "start" }), 30);
}

/* ---------------- SOS ---------------- */
export function sos(view) {
  view.innerHTML = `
    <div class="plate" aria-live="polite">
      <p class="lab">내 위치 (GPS, 데이터 없이도 잡혀요)</p>
      <p class="big" id="lat">찾는 중…</p><p class="big" id="lon"></p>
      <p class="dms" id="dms"></p><p class="acc" id="acc"></p>
    </div>
    <div class="script" id="script">119에 전화가 되면 산 이름, 출발한 곳, 다친 사람 상태와 함께 위 숫자를 불러 주세요.</div>
    <div class="btn-row">
      <button class="btn" id="whistle">호루라기 소리</button>
      <button class="btn ghost" id="flash">화면 깜빡이기</button>
    </div>
    <p class="small muted" style="margin-top:10px">통화가 끊기면 119로 문자를 보낼 수 있어요. 가까운 국가지점번호판(노란 판의 번호)도 함께 알려 주세요.</p>
    <div class="btn-row">
      <a class="btn ghost" href="#guide/lost">조난 행동 요령</a>
      <a class="btn ghost" href="#guide/aid">응급처치</a>
    </div>
    <div class="flash" id="fl"></div>`;
  keepScreenOn(true);
  const stop = watchPosition((p) => {
    const { latitude: la, longitude: lo, accuracy, altitude } = p.coords;
    $("#lat", view).textContent = `북위 ${la.toFixed(5)}`;
    $("#lon", view).textContent = `동경 ${lo.toFixed(5)}`;
    $("#dms", view).textContent = `${dms(la, "N", "S")}  ${dms(lo, "E", "W")}`;
    $("#acc", view).textContent = `정확도 약 ${Math.round(accuracy)}m${altitude != null ? `, 고도 약 ${Math.round(altitude)}m` : ""}, ${new Date().toLocaleTimeString("ko-KR")} 기준`;
    $("#script", view).innerHTML = `<b>119에 이렇게 말하세요</b><br>"산에서 도움이 필요해요. 제 위치는 북위 ${la.toFixed(5)}, 동경 ${lo.toFixed(5)}이고, 정확도는 약 ${Math.round(accuracy)}미터예요."`;
  }, (err) => {
    $("#lat", view).textContent = "위치를 못 찾았어요";
    $("#lon", view).textContent = "";
    $("#acc", view).textContent = posErrorText(err);
  });
  const wb = $("#whistle", view);
  const paintW = () => (wb.textContent = whistleOn() ? "호루라기 멈추기" : "호루라기 소리");
  wb.onclick = () => { whistleOn() ? stopWhistle() : startWhistle(); paintW(); };
  paintW();
  const fl = $("#fl", view);
  $("#flash", view).onclick = () => fl.classList.add("on");
  fl.onclick = () => fl.classList.remove("on");
  return () => { stop(); stopWhistle(); keepScreenOn(false); };
}
