// 静的 JSON の取得とキャッシュ。サーバーは無い。
//
// index.json     … 起動時に必ず読む（日付一覧・統計・ファセット）
// articles.json  … 記事一覧/検索に入ったとき
// news/<q>.json  … その四半期の日を開いたとき
// iocs.json      … IOC 画面に入ったとき

const BASE = new URL("../../data/", import.meta.url);

const cache = new Map();
const listeners = new Set();

export const state = {
  index: null,
  articles: null,
  iocs: null,
  quarters: new Map(),
};

export function onStatus(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

function status(message, busy) {
  for (const fn of listeners) fn(message, busy);
}

async function getJson(path, label) {
  if (cache.has(path)) return cache.get(path);
  const task = (async () => {
    status(`${label}を読み込んでいます…`, true);
    const res = await fetch(new URL(path, BASE), { cache: "default" });
    if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
    const json = await res.json();
    status("", false);
    return json;
  })();
  cache.set(path, task);
  try {
    return await task;
  } catch (e) {
    cache.delete(path);
    status(`${label}を読み込めませんでした`, false);
    throw e;
  }
}

export async function loadIndex() {
  if (!state.index) state.index = await getJson("index.json", "目次");
  return state.index;
}

export async function loadArticles() {
  if (!state.articles) {
    const data = await getJson("articles.json", "記事索引");
    state.articles = data.articles;
    for (const a of state.articles) a._h = `${a.t} ${a.s || ""} ${(a.c || []).join(" ")}`.toLowerCase();
  }
  return state.articles;
}

export async function loadQuarter(quarter) {
  if (!state.quarters.has(quarter)) {
    const data = await getJson(`news/${quarter}.json`, `${quarter} の本文`);
    const map = new Map();
    for (const day of data.days) map.set(day.date, day);
    state.quarters.set(quarter, map);
  }
  return state.quarters.get(quarter);
}

export async function loadDay(date) {
  const index = await loadIndex();
  const entry = index.days.find((d) => d.d === date);
  if (!entry) return null;
  const quarter = await loadQuarter(entry.q);
  return quarter.get(date) || null;
}

export async function loadIocs() {
  if (!state.iocs) {
    const data = await getJson("iocs.json", "IOC");
    const cols = data.columns;
    state.iocs = data.rows.map((row) => {
      const rec = {};
      cols.forEach((c, i) => { rec[c] = row[i]; });
      rec._h = `${rec.value} ${rec.actor} ${rec.malware} ${rec.category} ${rec.description}`.toLowerCase();
      return rec;
    });
  }
  return state.iocs;
}

/** 日付 → その日の記事一覧（index.json の目次だけで足りる用途向け）。 */
export function dayEntry(date) {
  return state.index?.days.find((d) => d.d === date) || null;
}

export function neighbours(date) {
  const days = state.index?.days || [];
  const at = days.findIndex((d) => d.d === date);
  return { prev: at > 0 ? days[at - 1].d : null, next: at >= 0 && at < days.length - 1 ? days[at + 1].d : null };
}
