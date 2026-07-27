// 起動・ルーティング・クローム。
//
// ルートは `#/<view>?<query>`。ポータル（research_bench）からの deep link も同じ形。
//   #/                     概要
//   #/news?q=…&year=…      記事一覧・検索
//   #/day/20260727[/3]     その日のまとめ（末尾は記事の位置）
//   #/ioc?q=…&type=…       IOC 一覧
//
// iframe に入っているとき（またはクエリに embed=1）は自前のヘッダーを畳む。
// research_bench の仕様 §4 でいう embed-mode。

import { el, num } from "./util.js";
import { loadIndex, onStatus } from "./store.js";
import { renderOverview } from "./view-overview.js";
import { renderNews } from "./view-news.js";
import { renderDay } from "./view-day.js";
import { renderIoc } from "./view-ioc.js";

const view = document.getElementById("view");
const statusEl = document.getElementById("status");

const ROUTES = {
  overview: renderOverview,
  news: renderNews,
  day: renderDay,
  ioc: renderIoc,
};

// ---------------------------------------------------------------- 埋め込み

const embedded = (() => {
  const params = new URLSearchParams(location.search);
  if (params.get("embed") === "1") return true;
  if (params.get("embed") === "0") return false;
  try {
    return window.self !== window.top;
  } catch {
    return true; // クロスオリジンで判定できない = 埋め込まれている
  }
})();

if (embedded) document.documentElement.dataset.embed = "1";

// ---------------------------------------------------------------- テーマ

const THEME_KEY = "tech-memo-daily-news:theme";

function applyTheme(theme) {
  if (theme === "light" || theme === "dark") document.documentElement.dataset.theme = theme;
  else delete document.documentElement.dataset.theme;
}

/** 埋め込み時は親（ポータル）のテーマ切り替えに追従する。同一オリジンのときだけ効く。 */
function followParentTheme() {
  if (!embedded) return false;
  try {
    const parentRoot = window.parent.document.documentElement;
    const apply = () => applyTheme(parentRoot.dataset.theme || "");
    apply();
    new MutationObserver(apply).observe(parentRoot, { attributes: true, attributeFilter: ["data-theme"] });
    return true;
  } catch {
    return false; // 別オリジン。prefers-color-scheme に任せる
  }
}

if (!followParentTheme()) applyTheme(localStorage.getItem(THEME_KEY));

document.getElementById("themeBtn")?.addEventListener("click", () => {
  const now = document.documentElement.dataset.theme;
  const next = now === "dark" ? "light" : now === "light" ? "" : "dark";
  applyTheme(next);
  if (next) localStorage.setItem(THEME_KEY, next);
  else localStorage.removeItem(THEME_KEY);
});

// ---------------------------------------------------------------- ルーター

export function parseHash(hash = location.hash) {
  const raw = String(hash || "").replace(/^#\/?/, "");
  const [pathPart, queryPart] = raw.split("?");
  // ポータルの deep link は {detail} を URL エンコードして埋めるので `20260722/0` が
  // `20260722%2F0` で届く。先に復号してから区切る。
  const segments = decodeSafe(pathPart).split("/").filter(Boolean);
  const name = segments[0] || "overview";
  return {
    name: ROUTES[name] ? name : "overview",
    segments: segments.slice(1),
    query: new URLSearchParams(queryPart || ""),
  };
}

function decodeSafe(text) {
  try {
    return decodeURIComponent(text);
  } catch {
    return text;
  }
}

export function go(path, { replace = false } = {}) {
  const target = path.startsWith("#") ? path : `#${path}`;
  if (location.hash === target) return;
  if (replace) history.replaceState(null, "", target);
  else location.hash = target;
  if (replace) render();
}

/** 現在のクエリを差分更新して履歴を汚さずに書き戻す。 */
export function setQuery(patch) {
  const route = parseHash();
  for (const [k, v] of Object.entries(patch)) {
    if (v === null || v === undefined || v === "") route.query.delete(k);
    else route.query.set(k, v);
  }
  const qs = route.query.toString();
  const path = ["#/" + route.name, ...route.segments].join("/") + (qs ? `?${qs}` : "");
  history.replaceState(null, "", path);
}

let token = 0;

async function render() {
  const route = parseHash();
  const mine = ++token;

  for (const tab of document.querySelectorAll(".tab")) {
    const active = tab.dataset.route === route.name
      || (route.name === "day" && tab.dataset.route === "news");
    tab.classList.toggle("is-active", active);
    if (active) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  }

  try {
    await ROUTES[route.name](view, route);
  } catch (err) {
    if (mine !== token) return;
    console.error(err);
    view.replaceChildren(el("div", { class: "empty" }, [
      el("h2", { text: "表示できませんでした" }),
      el("p", { text: String(err && err.message ? err.message : err) }),
      el("p", { class: "dim", text: "データ生成前の可能性があります: python3 daily-news/ui/build_ui_data.py" }),
    ]));
  }
}

window.addEventListener("hashchange", render);

onStatus((message, busy) => {
  statusEl.textContent = message || "";
  statusEl.classList.toggle("is-busy", Boolean(busy));
});

(async () => {
  try {
    const index = await loadIndex();
    const s = index.stats;
    document.getElementById("footerMeta").textContent =
      `${num(s.days)}日 / 記事 ${num(s.articles)} / IOC ${num(s.iocs)} — 更新 ${index.generated_at.slice(0, 10)}`;
  } catch {
    // render() 側で同じエラーを表示する
  }
  await render();
})();
