// Small shared helpers.
export const $ = (sel, el = document) => el.querySelector(sel);
export const $$ = (sel, el = document) => Array.from(el.querySelectorAll(sel));

export function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export function pct(p) {
  if (p >= 0.995) return "99%";
  if (p < 0.01) return "1% 미만";
  return Math.round(p * 100) + "%";
}

// verdict (도감 v) -> label and colour class
export const VERDICT = {
  edible: { label: "먹을 수 있음", cls: "safe" },
  edible_caution: { label: "손질·부위 주의", cls: "caution" },
  inedible: { label: "먹지 않음", cls: "unknown" },
  toxic: { label: "독초", cls: "danger" },
  deadly: { label: "맹독", cls: "deadly" },
  mushroom: { label: "버섯: 먹지 마세요", cls: "fungus" },
  other: { label: "모름", cls: "unknown" },
};

export function verdictOf(entry) {
  return VERDICT[entry?.v] || VERDICT.other;
}

export function badge(entry) {
  const v = verdictOf(entry);
  return `<span class="badge ${v.cls}">${esc(v.label)}</span>`;
}

let toastTimer = null;
export function toast(msg) {
  let t = document.querySelector(".toast");
  if (!t) {
    t = document.createElement("div");
    t.className = "toast";
    t.setAttribute("role", "status");
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), 2600);
}

export function fmtDate(ms) {
  const d = new Date(ms);
  const z = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}.${z(d.getMonth() + 1)}.${z(d.getDate())} ${z(d.getHours())}:${z(d.getMinutes())}`;
}

export function android() {
  return typeof window.AndroidApp !== "undefined" ? window.AndroidApp : null;
}

export function keepScreenOn(on) {
  try { android()?.keepScreenOn(!!on); } catch (_) { /* not in the Android shell */ }
}

export const ICONS = {
  camera: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>',
  book: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M5 4h10a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h10"/></svg>',
  pin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z"/><circle cx="12" cy="10" r="2.2"/></svg>',
  guide: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7z"/><path d="M12 8v5M12 16v.5"/></svg>',
  back: '<svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>',
};
