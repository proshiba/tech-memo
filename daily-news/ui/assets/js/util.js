// 小物。DOM 生成・整形・Markdown 風レンダラ。
// データはリポジトリ由来だが URL だけは外部入力なので、href は http(s) に限る。

export function el(tag, opts = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(opts)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "text") node.textContent = v;
    else if (k === "class") node.className = v;
    else if (k === "dataset") Object.assign(node.dataset, v);
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const c of [].concat(children)) {
    if (c === null || c === undefined || c === false) continue;
    node.append(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return node;
}


export function safeUrl(raw) {
  const url = String(raw || "").trim();
  if (!/^https?:\/\//i.test(url)) return null;
  return url;
}

export function link(href, text, extra = {}) {
  const url = safeUrl(href);
  if (!url) return el("span", { text: text ?? String(href ?? "") });
  return el("a", { href: url, target: "_blank", rel: "noopener noreferrer", text: text ?? url, ...extra });
}

// ---------------------------------------------------------------- 日付

export function isoDate(yyyymmdd) {
  const s = String(yyyymmdd || "");
  return s.length === 8 ? `${s.slice(0, 4)}-${s.slice(4, 6)}-${s.slice(6)}` : s;
}

const WEEKDAY = ["日", "月", "火", "水", "木", "金", "土"];

export function jpDate(yyyymmdd) {
  const s = String(yyyymmdd || "");
  if (s.length !== 8) return s;
  const y = +s.slice(0, 4), m = +s.slice(4, 6), d = +s.slice(6);
  const w = WEEKDAY[new Date(Date.UTC(y, m - 1, d)).getUTCDay()];
  return `${y}年${m}月${d}日(${w})`;
}


export function monthOf(yyyymmdd) {
  return String(yyyymmdd || "").slice(0, 6);
}

export function num(n) {
  return Number(n || 0).toLocaleString("ja-JP");
}

// ---------------------------------------------------------------- 文字列


export function defang(value) {
  return String(value || "")
    .replace(/^http/i, "hxxp")
    .replace(/\./g, "[.]");
}

/** 表示用の名前。`BlueNoroff (high confidence)` の確度注記と欠損値は畳む。 */
export function cleanName(raw) {
  const v = String(raw || "").replace(/\s*\((?:high|medium|low)\s+confidence\)/gi, "").trim();
  return v === "unknown" || v === "N/A" ? "" : v;
}

/** アクターとマルウェアを 1 列にまとめる。同じ名前なら重ねない。 */
export function actorMalware(actor, malware) {
  return [...new Set([cleanName(actor), cleanName(malware)].filter(Boolean))].join(" / ");
}

export function norm(s) {
  return String(s || "").toLowerCase();
}

/** 空白区切りの語を全て含むか（AND 検索）。 */
export function matchesTerms(haystack, terms) {
  for (const t of terms) if (!haystack.includes(t)) return false;
  return true;
}

export function terms(query) {
  return norm(query).split(/\s+/).filter(Boolean);
}

export function highlight(text, termList) {
  const src = String(text || "");
  if (!termList.length) return document.createTextNode(src);
  const lower = src.toLowerCase();
  const spans = [];
  for (const t of termList) {
    let from = 0;
    for (;;) {
      const at = lower.indexOf(t, from);
      if (at < 0) break;
      spans.push([at, at + t.length]);
      from = at + t.length;
    }
  }
  if (!spans.length) return document.createTextNode(src);
  spans.sort((a, b) => a[0] - b[0]);
  const merged = [spans[0]];
  for (const s of spans.slice(1)) {
    const last = merged[merged.length - 1];
    if (s[0] <= last[1]) last[1] = Math.max(last[1], s[1]);
    else merged.push(s);
  }
  const out = document.createDocumentFragment();
  let cursor = 0;
  for (const [a, b] of merged) {
    if (a > cursor) out.append(src.slice(cursor, a));
    out.append(el("mark", { text: src.slice(a, b) }));
    cursor = b;
  }
  if (cursor < src.length) out.append(src.slice(cursor));
  return out;
}

// ---------------------------------------------------------------- Markdown

const MD_LINK = /\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)/g;
const BARE_URL = /(?:https?|hxxps?):\/\/[^\s<>"'）」]+/g;
const CODE = /`([^`]+)`/g;
const BOLD = /\*\*([^*]+)\*\*/g;

/** 行内の記法（リンク・強調・コード）を要素に落とす。 */
export function inline(text) {
  const out = document.createDocumentFragment();
  const src = String(text ?? "");
  const marks = [];

  for (const re of [MD_LINK, BARE_URL, CODE, BOLD]) {
    re.lastIndex = 0;
    let m;
    while ((m = re.exec(src)) !== null) {
      marks.push({ at: m.index, end: m.index + m[0].length, re, m });
    }
  }
  marks.sort((a, b) => a.at - b.at || b.end - a.end);

  let cursor = 0;
  for (const mark of marks) {
    if (mark.at < cursor) continue;
    if (mark.at > cursor) out.append(src.slice(cursor, mark.at));
    const [whole, g1, g2] = mark.m;
    if (mark.re === MD_LINK) out.append(link(g2, g1 || g2));
    else if (mark.re === BARE_URL) {
      const url = safeUrl(whole);
      out.append(url ? link(url, whole) : el("span", { class: "defanged", text: whole }));
    } else if (mark.re === CODE) out.append(el("code", { text: g1 }));
    else out.append(el("strong", { text: g1 }));
    cursor = mark.end;
  }
  if (cursor < src.length) out.append(src.slice(cursor));
  return out;
}

/** [[階層, テキスト], …] を入れ子のリストに落とす。build_ui_data.py の出力形式。 */
export function renderBlock(rows, termList = []) {
  const root = el("ul", { class: "md-list" });
  const stack = [{ level: 1, node: root }];
  // ラベル行の直下は元 Markdown で 1 段下がっているので、最小の階層を 1 に寄せる。
  const levels = (rows || []).map(([lv]) => lv);
  const base = (levels.length ? Math.min(...levels) : 1) - 1;
  for (const [rawLevel, text] of rows || []) {
    const level = rawLevel - base;
    // 同じ階層は同じ ul に積む。深い階層から戻ってきたときだけ畳む。
    while (stack.length > 1 && stack[stack.length - 1].level > level) stack.pop();
    let host = stack[stack.length - 1].node;
    if (level > stack[stack.length - 1].level) {
      const items = host.children;
      const last = items[items.length - 1];
      const nested = el("ul", { class: "md-list" });
      (last || host).append(nested);
      host = nested;
      stack.push({ level, node: nested });
    }
    const li = el("li");
    li.append(termList.length ? highlightInline(text, termList) : inline(text));
    host.append(li);
  }
  return root;
}

function highlightInline(text, termList) {
  const src = String(text ?? "");
  if (MD_LINK.test(src) || BARE_URL.test(src)) {
    MD_LINK.lastIndex = BARE_URL.lastIndex = 0;
    return inline(src);
  }
  return highlight(src, termList);
}

/** 生 Markdown（節の本文・IOC 収集ログ）を描く。見出し・箇条書き・表に対応。 */
export function renderMarkdown(text) {
  const out = el("div", { class: "md" });
  const lines = String(text || "").split("\n");
  let list = null;
  let stack = [];
  let table = null;

  const closeList = () => { list = null; stack = []; };
  const closeTable = () => { table = null; };

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const line = raw.trimEnd();

    if (!line.trim()) { closeList(); closeTable(); continue; }

    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    if (heading) {
      closeList(); closeTable();
      const level = Math.min(6, heading[1].length + 1);
      const h = el(`h${level}`, { class: "md-h" });
      h.append(inline(heading[2]));
      out.append(h);
      continue;
    }

    if (/^\s*\|/.test(line)) {
      const cells = line.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
      if (cells.every((c) => /^:?-{2,}:?$/.test(c))) continue;
      closeList();
      if (!table) {
        table = el("table", { class: "md-table" });
        out.append(el("div", { class: "md-table-wrap" }, [table]));
        const head = el("tr");
        for (const c of cells) head.append(el("th", {}, [inline(c)]));
        table.append(el("thead", {}, [head]));
        table.append(el("tbody"));
        continue;
      }
      const tr = el("tr");
      for (const c of cells) tr.append(el("td", {}, [inline(c)]));
      table.querySelector("tbody").append(tr);
      continue;
    }
    closeTable();

    const bullet = /^(\s*)(?:[-*+]|\d+\.)\s+(.*)$/.exec(line);
    if (bullet) {
      const level = Math.floor(bullet[1].replace(/\t/g, "    ").length / 4) + 1;
      if (!list) {
        list = el("ul", { class: "md-list" });
        out.append(list);
        stack = [{ level: 1, node: list }];
      }
      while (stack.length > 1 && stack[stack.length - 1].level > level) stack.pop();
      let host = stack[stack.length - 1].node;
      if (level > stack[stack.length - 1].level) {
        const items = host.children;
        const last = items[items.length - 1];
        const nested = el("ul", { class: "md-list" });
        (last || host).append(nested);
        host = nested;
        stack.push({ level, node: nested });
      }
      host.append(el("li", {}, [inline(bullet[2])]));
      continue;
    }

    closeList();
    out.append(el("p", { class: "md-p" }, [inline(line)]));
  }
  return out;
}

// ---------------------------------------------------------------- その他

export async function copy(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

export function download(filename, text, mime = "text/plain;charset=utf-8") {
  const url = URL.createObjectURL(new Blob([text], { type: mime }));
  const a = el("a", { href: url, download: filename });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function debounce(fn, ms = 180) {
  let timer = 0;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}
