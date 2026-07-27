// 1 日分のまとめ。元の Markdown の構造（節と記事内のラベル）をそのまま出す。

import { el, num, jpDate, isoDate, link, renderBlock, renderMarkdown, copy, actorMalware } from "./util.js";
import { loadIndex, loadDay, loadIocs, neighbours } from "./store.js";

const SECTION_TITLES = {
  overview: "概要",
  issues: "課題",
  tools: "Tools",
  malware_campaign: "malware campaign",
  security_report: "security report",
  cybercrime: "cybercrime topics",
  jp_incidents: "日本のインシデント事例",
  memo: "その他のメモ",
};

const BLOCK_TITLES = {
  summary: "要約",
  ioc: "IOC の列挙",
  advice: "推奨事項",
  etc: "その他",
  gpt: "ChatGPT の推奨事項",
  note: "追記",
};

export async function renderDay(root, route) {
  const index = await loadIndex();
  const date = route.segments[0];
  const focus = route.segments[1];

  const day = date ? await loadDay(date) : null;
  if (!day) {
    root.replaceChildren(el("div", { class: "empty" }, [
      el("h2", { text: "その日のデータがありません" }),
      el("p", { text: date ? `${isoDate(date)} は収録されていません。` : "日付が指定されていません。" }),
      el("a", { class: "btn", href: "#/news", text: "ニュース一覧へ" }),
    ]));
    return;
  }

  const { prev, next } = neighbours(date);
  const entry = index.days.find((d) => d.d === date);
  const source = `https://github.com/proshiba/tech-memo/blob/main/daily-news/news/${day.quarter}/${date}.md`;

  const nav = el("div", { class: "day-nav" }, [
    prev ? el("a", { class: "btn ghost", href: `#/day/${prev}`, text: `← ${isoDate(prev)}` })
         : el("span", { class: "btn ghost is-disabled", text: "← 前の日" }),
    el("a", { class: "btn ghost", href: "#/news", text: "一覧" }),
    next ? el("a", { class: "btn ghost", href: `#/day/${next}`, text: `${isoDate(next)} →` })
         : el("span", { class: "btn ghost is-disabled", text: "次の日 →" }),
  ]);

  const page = el("section", { class: "page" }, [
    el("div", { class: "page-head row" }, [
      el("div", {}, [
        el("h1", { text: jpDate(date) }),
        el("p", { class: "lede" }, [
          el("span", { text: `記事 ${day.articles.length} 件` }),
          entry?.ioc ? el("span", { text: ` / IOC ${num(entry.ioc)} 件` }) : null,
          el("span", { text: " — " }),
          link(source, "元の Markdown"),
        ]),
      ]),
      nav,
    ]),
  ]);

  // 記事の前に置かれる節（Tools / campaign / report / cybercrime）
  for (const key of ["overview", "issues", "tools", "malware_campaign", "security_report", "cybercrime"]) {
    if (day.sections[key]) page.append(sectionCard(key, day.sections[key], key === "malware_campaign"));
  }

  if (day.articles.length) {
    page.append(el("h2", { class: "sec-title", id: "articles", text: "日々のニュース要約" }));
    const list = el("div", { class: "day-articles" });
    day.articles.forEach((art, i) => list.append(articleBlock(art, i, date, String(i) === focus)));
    page.append(list);
  }

  for (const key of ["jp_incidents", "memo"]) {
    if (day.sections[key]) page.append(sectionCard(key, day.sections[key]));
  }

  page.append(iocPanel(date, entry, day));
  page.append(nav.cloneNode(true));

  root.replaceChildren(page);

  if (focus !== undefined) {
    const target = page.querySelector(`#article-${CSS.escape(String(focus))}`);
    target?.scrollIntoView({ block: "start" });
  } else {
    root.scrollTop = 0;
  }
}

function sectionCard(key, markdown, collapsed = false) {
  const body = renderMarkdown(markdown);
  if (!collapsed) {
    return el("section", { class: "card" }, [
      el("h2", { class: "card-title", text: SECTION_TITLES[key] || key }),
      body,
    ]);
  }
  const details = el("details", { class: "card card-fold", open: markdown.length < 2000 });
  details.append(el("summary", { class: "card-title" }, [
    el("span", { text: SECTION_TITLES[key] || key }),
    el("span", { class: "dim small", text: `${Math.round(markdown.length / 100) / 10}k 文字` }),
  ]));
  details.append(body);
  return details;
}

function articleBlock(art, i, date, focused) {
  const head = el("div", { class: "article-head" }, [
    el("h3", { class: "article-h" }, [
      el("a", { class: "anchor", href: `#/day/${date}/${i}`, title: "この記事へのリンク", text: "#" }),
      el("span", { text: art.title || "（無題）" }),
    ]),
    art.url ? el("p", { class: "article-src" }, [link(art.url, art.url)]) : null,
  ]);

  const node = el("article", {
    class: "article-full" + (focused ? " is-focus" : ""),
    id: `article-${i}`,
  }, [head]);

  if (art.cve?.length) {
    node.append(el("div", { class: "chips" }, art.cve.map((cve) =>
      el("a", { class: "chip chip-cve", href: `#/news?q=${encodeURIComponent(cve)}`, text: cve }))));
  }

  for (const key of ["summary", "ioc", "advice", "etc", "gpt", "note"]) {
    if (!art[key]) continue;
    const rows = art[key];
    // IOC を大量に列挙している記事（キャンペーンのドメイン一覧など）は畳んでおく。
    if (key === "ioc" && rows.length > 12) {
      node.append(el("details", { class: `block block-${key} card-fold` }, [
        el("summary", { class: "block-title", text: `${BLOCK_TITLES[key]}（${num(rows.length)} 行）` }),
        renderBlock(rows),
      ]));
      continue;
    }
    node.append(el("div", { class: `block block-${key}` }, [
      el("h4", { class: "block-title", text: BLOCK_TITLES[key] }),
      renderBlock(rows),
    ]));
  }
  return node;
}

/** その日に収集した IOC。件数が多いので既定は畳んでおく。 */
function iocPanel(date, entry, day) {
  const wrap = el("section", { class: "card" });
  const count = entry?.ioc || 0;

  wrap.append(el("h2", { class: "card-title" }, [
    el("span", { text: "この日に収集した IOC" }),
    el("span", { class: "dim small", text: count ? `${num(count)} 件` : "なし" }),
  ]));

  if (!count) {
    wrap.append(el("p", { class: "dim", text: "この日の IOC 収集はまだ行われていません。" }));
    if (day.ioc_log) wrap.append(logFold(day.ioc_log));
    return wrap;
  }

  const table = el("div", { class: "table-wrap" }, [el("p", { class: "dim", text: "読み込み中…" })]);
  const fold = el("details", { class: "card-fold sub", open: count <= 15 }, [
    el("summary", { class: "card-title", text: `一覧を開く（${num(count)} 件）` }),
    table,
  ]);

  wrap.append(el("div", { class: "row-actions" }, [
    el("a", { class: "btn", href: `#/ioc?news=${date}`, text: "IOC 画面で開く" }),
  ]), fold);
  if (day.ioc_log) wrap.append(logFold(day.ioc_log));

  loadIocs().then((rows) => {
    const mine = rows.filter((r) => r.news_date === date);
    table.replaceChildren(compactIocTable(mine));
  }).catch(() => {
    table.replaceChildren(el("p", { class: "dim", text: "IOC を読み込めませんでした。" }));
  });

  return wrap;
}

function logFold(markdown) {
  const details = el("details", { class: "card-fold sub" });
  details.append(el("summary", { class: "card-title", text: "IOC 収集作業ログ" }));
  details.append(renderMarkdown(markdown));
  return details;
}

function compactIocTable(rows) {
  if (!rows.length) return el("p", { class: "dim", text: "該当なし" });
  const table = el("table", { class: "table" }, [
    el("thead", {}, [el("tr", {}, [
      el("th", { text: "種別" }), el("th", { text: "値" }),
      el("th", { text: "分類" }), el("th", { text: "アクター / マルウェア" }), el("th", { text: "" }),
    ])]),
  ]);
  const body = el("tbody");
  for (const r of rows.slice(0, 200)) {
    body.append(el("tr", {}, [
      el("td", { class: "nowrap" }, [el("span", { class: `pill pill-${r.type.replace(".", "-")}`, text: shortType(r.type) })]),
      el("td", { class: "mono value-cell" }, [
        el("span", { text: r.value }),
        el("button", { class: "icon-btn", type: "button", title: "コピー", text: "⧉", onclick: (e) => copyValue(e, r.value) }),
      ]),
      el("td", { text: r.category }),
      el("td", { text: actorMalware(r.actor, r.malware) }),
      el("td", {}, [r.reference ? link(r.reference, "出典") : null]),
    ]));
  }
  table.append(body);
  const out = el("div", {}, [table]);
  if (rows.length > 200) {
    out.append(el("p", { class: "dim small", text: `先頭 200 件を表示（全 ${num(rows.length)} 件）。残りは IOC 画面で。` }));
  }
  return out;
}

export function shortType(type) {
  return String(type).replace(/^ioc\./, "");
}

async function copyValue(event, value) {
  const ok = await copy(value);
  const btn = event.currentTarget;
  btn.textContent = ok ? "✓" : "×";
  setTimeout(() => { btn.textContent = "⧉"; }, 900);
}
