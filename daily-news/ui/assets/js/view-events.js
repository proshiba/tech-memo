// イベント。記事本文を daily-news/data 側で構造化したものを、分類軸で絞って見る。
//
// ポータルからの deep link は #/events?actor=… / ?malware=… / ?product=… で入ってくる。

import { el, num, jpDate, isoDate, monthOf, link, terms, matchesTerms,
         highlight, debounce } from "./util.js";
import { loadIndex, loadEvents, tagLabel, dimensions } from "./store.js";
import { setQuery } from "./main.js";
import { toggle, selectField } from "./controls.js";

const PAGE = 40;

// 絞り込みに出す次元。event_type は種別そのものなので別扱いにする。
const TAG_DIMENSIONS = ["initial_access", "actor", "actor_attribution", "malware",
                        "product", "product_class", "attack_method", "crime_trend"];

const CONFIDENCE_LABEL = { h: "高", m: "中", l: "低" };

/** 動的な次元の表記ゆれ（teampcp / team_pcp）を吸収する。build 側のファセットと同じ潰し方。 */
const squash = (v) => String(v || "").toLowerCase().replace(/[^a-z0-9]+/g, "");

export async function renderEvents(root, route) {
  const index = await loadIndex();
  const events = await loadEvents();
  const dims = new Map(dimensions().map((d) => [d.key, d]));
  const dynamic = new Set(dimensions().filter((d) => d.mode === "dynamic").map((d) => d.key));

  const active = readFilters(route.query);

  const filters = el("form", { class: "filters", onsubmit: (e) => e.preventDefault() }, [
    el("div", { class: "field field-grow" }, [
      el("label", { class: "field-label", for: "evQ", text: "検索" }),
      el("input", {
        id: "evQ", type: "search", class: "input", value: active.q, autocomplete: "off",
        placeholder: "タイトル・要約・タグ（空白区切りで AND）",
        oninput: debounce((e) => update({ q: e.target.value }), 200),
      }),
    ]),
    facetField("種別", "event_type", index, active, update, dims),
    ...TAG_DIMENSIONS.map((d) => facetField(dims.get(d)?.label || d, d, index, active, update, dims)),
    selectField("evMonth", "月", monthOptions(index), active.month, (v) => update({ month: v })),
    el("div", { class: "field field-checks" }, [
      toggle("要確認のみ", active.review, (v) => update({ review: v ? "1" : "" })),
      toggle("月次フォロー候補", active.followup, (v) => update({ followup: v ? "1" : "" })),
    ]),
  ]);

  const summary = el("div", { class: "result-bar" });
  const list = el("div", { class: "event-list" });
  const more = el("button", { class: "btn more", type: "button" });

  root.replaceChildren(el("section", { class: "page" }, [
    el("div", { class: "page-head" }, [
      el("h1", { text: "イベント" }),
      el("p", { class: "lede" }, [
        el("span", { text: `記事本文から起こした構造化イベント ${num(index.stats.events)} 件（${isoDate(index.stats.first_event)} 〜）。9 つの分類軸で絞り込める。` }),
      ]),
    ]),
    filters,
    summary,
    list,
    more,
  ]));

  function update(patch) {
    setQuery(patch);
    draw(readFilters(new URLSearchParams(location.hash.split("?")[1] || "")));
  }

  function draw(f) {
    const t = terms(f.q);
    const hits = events.filter((ev) => {
      if (f.month && monthOf(ev.d) !== f.month) return false;
      if (f.event_type && ev.e !== f.event_type) return false;
      if (f.review && !ev.r) return false;
      if (f.followup && ev.f !== "yes") return false;
      for (const dim of TAG_DIMENSIONS) {
        if (!f[dim]) continue;
        const values = ev._dim.get(dim) || [];
        const hit = dynamic.has(dim)
          ? values.some((v) => squash(v) === squash(f[dim]))
          : values.includes(f[dim]);
        if (!hit) return false;
      }
      return !t.length || matchesTerms(ev._h, t);
    });
    hits.reverse(); // 新しい日から

    summary.replaceChildren(
      el("p", { class: "result-count", text: hits.length ? `${num(hits.length)} 件` : "一致するイベントはありません" }),
      el("div", { class: "row-actions" }, [activeChips(f, update, dims)]),
    );

    if (!hits.length) summary.append(fallbackHint(f));

    let shown = 0;
    list.replaceChildren();
    const step = () => {
      const slice = hits.slice(shown, shown + PAGE);
      list.append(...slice.map((ev) => eventCard(ev, t, update, dims)));
      shown += slice.length;
      more.hidden = shown >= hits.length;
      more.textContent = `さらに表示（残り ${num(hits.length - shown)} 件）`;
    };
    more.onclick = step;
    step();
  }

  draw(active);
}

function readFilters(query) {
  const f = {
    q: query.get("q") || "",
    month: query.get("month") || "",
    event_type: query.get("event_type") || query.get("type") || "",
    review: query.get("review") === "1",
    followup: query.get("followup") === "1",
  };
  for (const dim of TAG_DIMENSIONS) f[dim] = query.get(dim) || "";
  return f;
}

function eventCard(ev, termList, update, dims) {
  const head = el("div", { class: "event-head" }, [
    el("span", { class: `pill pill-${ev.e}`, text: tagLabel("event_type", ev.e) }),
    el("a", { class: "event-date", href: `#/day/${ev.d}`, title: jpDate(ev.d), text: isoDate(ev.d) }),
    ev.c && ev.c !== "h" ? el("span", { class: "chip chip-soft", text: `確度 ${CONFIDENCE_LABEL[ev.c]}` }) : null,
    ev.r ? el("span", { class: "chip chip-warn", text: "要確認" }) : null,
    ev.f === "yes" ? el("span", { class: "chip chip-soft", text: "月次フォロー候補" }) : null,
  ]);

  const title = el("h3", { class: "event-title" });
  title.append(highlight(ev.t, termList));

  const body = el("p", { class: "event-summary" });
  body.append(highlight(ev.s, termList));

  const links = el("div", { class: "event-links" }, [
    ev.a
      ? el("a", { class: "btn ghost small", href: `#/day/${ev.a[0]}/${ev.a[1]}`, text: "元の記事" })
      : el("span", { class: "dim small", text: "記事節に対応なし" }),
    ev.u ? link(ev.u, "一次ソース", { class: "btn ghost small" }) : null,
  ]);

  const card = el("article", { class: "event-card" }, [head, title, body]);

  // タグは次元ごとにまとめる。押すとその値で絞り込む。
  const grouped = new Map();
  for (const [dim, normalized, raw, conf, note] of ev.g || []) {
    if (!grouped.has(dim)) grouped.set(dim, []);
    grouped.get(dim).push({ normalized, raw, conf, note });
  }
  if (grouped.size) {
    const tags = el("div", { class: "tag-groups" });
    for (const dim of ["event_type", ...TAG_DIMENSIONS]) {
      const items = grouped.get(dim);
      if (!items) continue;
      tags.append(el("div", { class: "tag-group" }, [
        el("span", { class: "tag-dim", text: dims.get(dim)?.label || dim }),
        el("div", { class: "chips" }, items.map((it) =>
          el("button", {
            class: "chip chip-link", type: "button",
            title: [it.raw, it.note].filter(Boolean).join(" — ") || it.normalized,
            onclick: () => update({ [dim]: it.normalized }),
          }, [el("span", { text: tagLabel(dim, it.normalized) })]))),
      ]));
    }
    card.append(tags);
  }

  card.append(links);
  return card;
}

/** 一致 0 件のとき、同じ名前を IOC 側で探せることを示す。 */
function fallbackHint(f) {
  const name = f.malware || f.actor;
  if (!name) return el("span");
  const key = f.malware ? "malware" : "actor";
  return el("p", { class: "dim small" }, [
    el("span", { text: `「${name}」のイベントはありません。` }),
    el("a", { href: `#/ioc?${key}=${encodeURIComponent(name)}`, text: " IOC 側で探す →" }),
  ]);
}

function activeChips(f, update, dims) {
  const chips = el("div", { class: "chips" });
  const labels = { q: "検索", month: "月", event_type: "種別" };
  for (const dim of TAG_DIMENSIONS) labels[dim] = dims.get(dim)?.label || dim;
  for (const [key, label] of Object.entries(labels)) {
    if (!f[key]) continue;
    chips.append(el("button", {
      class: "chip chip-active", type: "button", title: "この絞り込みを外す",
      onclick: () => update({ [key]: "" }),
    }, [el("span", { text: `${label}: ${tagLabel(key, f[key])}` }), el("b", { text: "×" })]));
  }
  for (const [key, label] of [["review", "要確認のみ"], ["followup", "月次フォロー候補"]]) {
    if (!f[key]) continue;
    chips.append(el("button", {
      class: "chip chip-active", type: "button", title: "この絞り込みを外す",
      onclick: () => update({ [key]: "" }),
    }, [el("span", { text: label }), el("b", { text: "×" })]));
  }
  return chips;
}

function facetField(label, dim, index, active, update, dims) {
  const pairs = index.event_facets?.[dim] || [];
  const options = [["", "すべて"], ...pairs.slice(0, 200).map(([value, count]) =>
    [value, `${tagLabel(dim, value)} (${count})`])];
  return selectField(`ev-${dim}`, label, options, active[dim], (v) => update({ [dim]: v }),
    { title: dims.get(dim)?.description || "" });
}

function monthOptions(index) {
  const months = [...new Set(index.days.filter((d) => d.ev).map((d) => monthOf(d.d)))]
    .sort().reverse();
  return [["", "すべて"], ...months.map((m) => [m, `${m.slice(0, 4)}-${m.slice(4)}`])];
}
