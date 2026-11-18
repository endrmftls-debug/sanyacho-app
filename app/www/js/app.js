// Boot + hash router for the offline app.
import { $, ICONS, esc } from "./util.js";
import { loadData, entry } from "./data.js";
import { loadAI } from "./ai.js";
import * as S from "./screens.js";

const TABS = [
  ["#home", "확인", ICONS.camera],
  ["#book", "도감", ICONS.book],
  ["#journal", "일지", ICONS.pin],
  ["#guide", "가이드", ICONS.guide],
];

let cleanup = null;

function frame() {
  document.body.innerHTML = `
    <header class="bar">
      <button class="back" id="back" aria-label="뒤로" hidden>${ICONS.back}</button>
      <span class="title" id="title">산야초 길잡이</span>
      <a class="sos-chip" href="#sos" aria-label="SOS 긴급 위치와 구조 요청">SOS</a>
    </header>
    <main id="view" tabindex="-1"></main>
    <nav class="tabs" aria-label="메뉴">${TABS.map(([h, l, i]) => `<a href="${h}" data-tab="${h}">${i}<span>${l}</span></a>`).join("")}</nav>`;
  $("#back").onclick = () => history.back();
}

function route() {
  if (cleanup) {
    try { cleanup(); } catch (_) { /* ignore */ }
    cleanup = null;
  }
  const raw = location.hash || "#home";
  const [path, qs] = raw.split("?");
  const query = new URLSearchParams(qs || "");
  const parts = path.slice(1).split("/");
  const view = $("#view");
  const name = parts[0] || "home";
  const titles = { home: "산야초 길잡이", camera: "사진 찍기", result: "판정 결과", book: "도감", journal: "채집 일지",
    find: "기록", guide: "생존 가이드", sos: "SOS 긴급" };
  let title = titles[name] || "산야초 길잡이";
  let tab = { home: "#home", camera: "#home", result: "#home", book: "#book", sp: "#book", journal: "#journal",
    find: "#journal", guide: "#guide" }[name] || "";
  view.scrollTop = 0;
  window.scrollTo(0, 0);
  switch (name) {
    case "camera": cleanup = S.camera(view); break;
    case "result": cleanup = S.result(view); break;
    case "sp": title = entry(parts[1])?.ko || "도감"; cleanup = S.species(view, parts[1], query); break;
    case "book": cleanup = S.book(view); break;
    case "journal": cleanup = S.journal(view); break;
    case "find": cleanup = S.find(view, parts[1]); break;
    case "guide": cleanup = S.guide(view, parts[1]); break;
    case "sos": cleanup = S.sos(view); break;
    default: cleanup = S.home(view);
  }
  $("#title").textContent = title;
  document.querySelector(".sos-chip").hidden = name === "sos";
  $("#back").hidden = name === "home" || name === "" || (TABS.some(([h]) => h === "#" + name) && !parts[1]);
  document.querySelectorAll("[data-tab]").forEach((a) => {
    if (a.dataset.tab === tab) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  if (typeof cleanup !== "function") cleanup = null;
}

// Android back button: go back inside the app, or let the app close on the home screen.
window.appBack = () => {
  const h = location.hash || "#home";
  if (h === "#home") return false;
  if (history.length > 1) history.back();
  else location.hash = "#home";
  return true;
};
// The camera screen handles pause/resume itself (it must stay open while Android shows the permission box).
window.appPause = () => {};
window.appResume = null;

async function boot() {
  frame();
  try {
    await loadData();
  } catch (e) {
    $("#view").innerHTML = `<p class="alert">도감 데이터를 읽지 못했어요: ${esc(e.message || e)}</p>`;
    return;
  }
  window.addEventListener("hashchange", route);
  route();
  setTimeout(loadAI, 400);
}

boot();
