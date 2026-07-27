// IOC 一覧。iocs.json の全件をブラウザ内で絞り込む。
//
// ポータルからの deep link は #/ioc?q=<値> / ?actor=… / ?malware=… で入ってくる。

import { el, num, isoDate, jpDate, link, copy, defang, terms, matchesTerms,
         debounce, download, norm, cleanName } from "./util.js";
import { loadIndex, loadIocs } from "./store.js";
import { setQuery } from "./main.js";

const PAGE = 200;

const SORTS = {
  date: (a, b) => (b.date || b.news_date).localeCompare(a.date || a.news_date),
  type: (a, b) => a.type.localeCompare(b.type) || a.value.localeCompare(b.value),
  value: (a, b) => a.value.localeCompare(b.value),
  actor: (a, b) => a.actor.localeCompare(b.actor) || a.value.localeCompare(b.value),
};

export async function renderIoc(root, route) {
  const index = await loadIndex();
  const rows = await loadIocs();

  const f = readFilters(route.query);

  const filters = el("form", { class: "filters", onsubmit: (e) => e.preventDefault() }, [
    el("div", { class: "field field-grow" }, [
      el("label", { class: "field-label", for: "iocQ", text: "検索" }),
      el("input", {
        id: "iocQ", type: "search", class: "input", value: f.q, autocomplete: "off",
        placeholder: "値・アクター・マルウェア・説明（空白区切りで AND）",
        oninput: debounce((e) => update({ q: e.target.value }), 200),
      }),
    ]),
    field("種別", "iocType", facetOptions(index.facets.type, (t) => t.replace(/^ioc\./, "")), f.type, (v) => update({ type: v })),
    field("分類", "iocCat", facetOptions(index.facets.category), f.category, (v) => update({ category: v })),
    field("アクター", "iocActor", facetOptions(index.facets.actor, null, 120), f.actor, (v) => update({ actor: v })),
    field("マルウェア", "iocMal", facetOptions(index.facets.malware, null, 120), f.malware, (v) => update({ malware: v })),
    el("div", { class: "field field-checks" }, [
      toggle("defang 表示", f.defang, (v) => update({ defang: v ? "1" : "" })),
    ]),
  ]);

  const summary = el("div", { class: "result-bar" });
  const host = el("div", { class: "table-wrap" });
  const more = el("button", { class: "btn more", type: "button" });

  root.replaceChildren(el("section", { class: "page" }, [
    el("div", { class: "page-head" }, [
      el("h1", { text: "IOC" }),
      el("p", { class: "lede", text: `記事の一次ソースを当たって収集した ${num(index.stats.iocs)} 件。値・アクター・マルウェアで絞り込める。` }),
    ]),
    filters,
    summary,
    host,
    more,
  ]));

  function update(patch) {
    setQuery(patch);
    draw(readFilters(new URLSearchParams(location.hash.split("?")[1] || "")));
  }

  function draw(active) {
    const t = terms(active.q);
    const hits = rows.filter((r) => {
      if (active.type && r.type !== active.type) return false;
      if (active.category && r.category !== active.category) return false;
      if (active.news && r.news_date !== active.news) return false;
      if (active.actor && !hasName(r.actor, active.actor)) return false;
      if (active.malware && !hasName(r.malware, active.malware)) return false;
      return !t.length || matchesTerms(r._h, t);
    });
    hits.sort(SORTS[active.sort] || SORTS.date);

    const empty = !hits.length;
    summary.replaceChildren(
      el("p", { class: "result-count", text: hits.length ? `${num(hits.length)} 件` : "一致する IOC はありません" }),
      el("div", { class: "row-actions" }, [
        activeChips(active, update),
        el("button", {
          class: "btn", type: "button", text: "CSV を書き出す",
          onclick: () => exportCsv(hits, active),
        }),
      ]),
    );
    if (empty) summary.append(fallbackHint(active));

    let shown = 0;
    const table = buildTable(active, update);
    const body = table.querySelector("tbody");
    host.replaceChildren(table);

    const step = () => {
      for (const r of hits.slice(shown, shown + PAGE)) body.append(rowNode(r, active));
      shown = Math.min(shown + PAGE, hits.length);
      more.hidden = shown >= hits.length;
      more.textContent = `さらに表示（残り ${num(hits.length - shown)} 件）`;
    };
    more.onclick = step;
    step();
  }

  draw(f);
}

function readFilters(query) {
  return {
    q: query.get("q") || "",
    type: query.get("type") || "",
    category: query.get("category") || "",
    actor: query.get("actor") || "",
    malware: query.get("malware") || "",
    news: query.get("news") || "",
    sort: query.get("sort") || "date",
    defang: query.get("defang") === "1",
  };
}

/** `Vidar Stealer, XMRig` のような複合値にも当てる。 */
function hasName(raw, wanted) {
  const target = norm(wanted);
  return norm(raw).split(/\s*[,/、]\s*/).some((n) => n.trim() === target) || norm(raw) === target;
}

function buildTable(active, update) {
  const head = el("tr");
  const columns = [
    ["type", "種別"], ["value", "値"], ["date", "観測日"],
    [null, "分類"], ["actor", "アクター"], [null, "マルウェア"],
    [null, "説明"], [null, "出典 / 収集日"],
  ];
  for (const [sortKey, label] of columns) {
    if (!sortKey) { head.append(el("th", { text: label })); continue; }
    head.append(el("th", {}, [
      el("button", {
        class: "th-sort" + (active.sort === sortKey ? " is-active" : ""),
        type: "button", text: label,
        onclick: () => update({ sort: sortKey }),
      }),
    ]));
  }
  return el("table", { class: "table table-ioc" }, [
    el("thead", {}, [head]),
    el("tbody"),
  ]);
}

function rowNode(r, active) {
  const shown = active.defang ? defang(r.value) : r.value;
  return el("tr", {}, [
    el("td", { class: "nowrap" }, [el("span", { class: "pill", text: r.type.replace(/^ioc\./, "") })]),
    el("td", { class: "mono value-cell" }, [
      el("span", { class: "value", text: shown }),
      el("button", {
        class: "icon-btn", type: "button", title: "コピー", text: "⧉",
        onclick: (e) => copyValue(e, shown),
      }),
    ]),
    el("td", { class: "nowrap", text: r.date || "" }),
    el("td", { text: r.category }),
    el("td", {}, [el("span", { class: "clamp", title: r.actor, text: cleanName(r.actor) })]),
    el("td", {}, [el("span", { class: "clamp", title: r.malware, text: cleanName(r.malware) })]),
    el("td", { class: "desc" }, [el("span", { class: "clamp", title: r.description, text: r.description })]),
    el("td", { class: "nowrap" }, [
      r.reference ? link(r.reference, "出典") : null,
      el("a", { class: "src-day", href: `#/day/${r.news_date}`, title: jpDate(r.news_date), text: isoDate(r.news_date) }),
    ]),
  ]);
}

/** IOC に無い名前は、イベント側に居ることがある。 */
function fallbackHint(active) {
  const name = active.malware || active.actor;
  if (!name) return el("span");
  const key = active.malware ? "malware" : "actor";
  return el("p", { class: "dim small" }, [
    el("span", { text: `「${name}」の IOC はありません。` }),
    el("a", { href: `#/events?${key}=${encodeURIComponent(name)}`, text: " イベント側で探す →" }),
  ]);
}

function activeChips(active, update) {
  const chips = el("div", { class: "chips" });
  const labels = {
    type: "種別", category: "分類", actor: "アクター",
    malware: "マルウェア", news: "収集日", q: "検索",
  };
  for (const [key, label] of Object.entries(labels)) {
    if (!active[key]) continue;
    chips.append(el("button", {
      class: "chip chip-active", type: "button",
      title: "この絞り込みを外す",
      onclick: () => update({ [key]: "" }),
    }, [el("span", { text: `${label}: ${active[key]}` }), el("b", { text: "×" })]));
  }
  return chips;
}

function exportCsv(rows, active) {
  const columns = ["type", "value", "date", "category", "actor", "actor_attribute",
                   "malware", "malware_type", "reference", "description", "confidence", "news_date"];
  const escape = (v) => {
    const s = String(v ?? "");
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const lines = [columns.join(",")];
  for (const r of rows) lines.push(columns.map((c) => escape(c === "value" && active.defang ? defang(r.value) : r[c])).join(","));
  download(`daily-news-iocs-${new Date().toISOString().slice(0, 10)}.csv`, lines.join("\n") + "\n", "text/csv;charset=utf-8");
}

function facetOptions(pairs, transform, limit = 60) {
  const items = (pairs || []).filter(([name]) => name).slice(0, limit);
  return [["", "すべて"], ...items.map(([name, count]) =>
    [name, `${transform ? transform(name) : name} (${count})`])];
}

function field(label, id, options, value, onchange) {
  const node = el("select", { id, class: "input", onchange: (e) => onchange(e.target.value) },
    options.map(([v, t]) => el("option", { value: v, text: t })));
  node.value = value;
  if (value && node.value !== value) {
    // ファセット上位に無い値が deep link で来た場合も選べるようにする
    node.append(el("option", { value, text: value }));
    node.value = value;
  }
  return el("div", { class: "field" }, [
    el("label", { class: "field-label", for: id, text: label }),
    node,
  ]);
}

function toggle(label, checked, onchange) {
  const input = el("input", { type: "checkbox", checked, onchange: (e) => onchange(e.target.checked) });
  return el("label", { class: "check" }, [input, el("span", { text: label })]);
}

async function copyValue(event, value) {
  const ok = await copy(value);
  const btn = event.currentTarget;
  btn.textContent = ok ? "✓" : "×";
  setTimeout(() => { btn.textContent = "⧉"; }, 900);
}
