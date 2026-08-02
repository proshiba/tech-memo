// 記事一覧と横断検索。articles.json（全期間の軽量索引）だけで動く。
// 本文は日ごとの画面（#/day/…）で四半期ファイルを遅延ロードして出す。

import { el, num, jpDate, isoDate, monthOf, terms, matchesTerms, highlight, debounce } from "./util.js";
import { loadIndex, loadArticles } from "./store.js";
import { toggle, selectField } from "./controls.js";
import { setQuery } from "./main.js";

const PAGE = 60;

export async function renderNews(root, route) {
  const index = await loadIndex();
  const articles = await loadArticles();

  const q = route.query.get("q") || "";
  const month = route.query.get("month") || "";
  const year = route.query.get("year") || "";
  const onlyIoc = route.query.get("ioc") === "1";
  const onlyCve = route.query.get("cve") === "1";

  const years = [...new Set(index.days.map((d) => d.d.slice(0, 4)))].sort().reverse();

  const filters = el("form", { class: "filters", onsubmit: (e) => e.preventDefault() }, [
    el("div", { class: "field field-grow" }, [
      el("label", { class: "field-label", for: "newsQ", text: "検索" }),
      el("input", {
        id: "newsQ", type: "search", class: "input", value: q, autocomplete: "off",
        placeholder: "タイトル・要約・CVE 番号（空白区切りで AND）",
        oninput: debounce((e) => update({ q: e.target.value }), 200),
      }),
    ]),
    selectField("newsYear", "年", [["", "すべて"], ...years.map((y) => [y, `${y}年`])], year,
      (v) => update({ year: v, month: "" })),
    selectField("newsMonth", "月", monthOptions(index, year), month, (v) => update({ month: v })),
    el("div", { class: "field field-checks" }, [
      toggle("IOCあり", onlyIoc, (v) => update({ ioc: v ? "1" : "" })),
      toggle("CVE言及", onlyCve, (v) => update({ cve: v ? "1" : "" })),
    ]),
  ]);

  const summary = el("p", { class: "result-count" });
  const list = el("div", { class: "article-list" });
  const more = el("button", { class: "btn more", type: "button", text: "さらに表示" });

  root.replaceChildren(el("section", { class: "page" }, [
    el("div", { class: "page-head" }, [
      el("h1", { text: "ニュース" }),
      el("p", { class: "lede", text: `${isoDate(index.stats.first_day)} 以降の ${num(index.stats.articles)} 記事を横断して探す。` }),
    ]),
    filters,
    summary,
    list,
    more,
  ]));

  function update(patch) {
    setQuery(patch);
    const next = new URLSearchParams(location.hash.split("?")[1] || "");
    draw({
      q: next.get("q") || "",
      month: next.get("month") || "",
      year: next.get("year") || "",
      onlyIoc: next.get("ioc") === "1",
      onlyCve: next.get("cve") === "1",
    });
    if (patch.year !== undefined || patch.month !== undefined) {
      const monthSelect = filters.querySelector("#newsMonth");
      const wanted = monthOptions(index, next.get("year") || "");
      monthSelect.replaceChildren(...wanted.map(([v, t]) => el("option", { value: v, text: t })));
      monthSelect.value = next.get("month") || "";
    }
  }

  function draw(f) {
    const t = terms(f.q);
    const hits = articles.filter((a) => {
      if (f.year && !a.d.startsWith(f.year)) return false;
      if (f.month && monthOf(a.d) !== f.month) return false;
      if (f.onlyIoc && !a.k) return false;
      if (f.onlyCve && !a.c) return false;
      return !t.length || matchesTerms(a._h, t);
    });
    hits.reverse(); // 新しい日から

    summary.textContent = hits.length
      ? `${num(hits.length)} 件${f.q ? `（「${f.q}」に一致）` : ""}`
      : "一致する記事はありません";

    let shown = 0;
    list.replaceChildren();
    const step = () => {
      const slice = hits.slice(shown, shown + PAGE);
      list.append(...groupByDay(slice, t));
      shown += slice.length;
      more.hidden = shown >= hits.length;
      more.textContent = `さらに表示（残り ${num(hits.length - shown)} 件）`;
    };
    more.onclick = step;
    step();
  }

  draw({ q, month, year, onlyIoc, onlyCve });
}

function groupByDay(articles, termList) {
  const out = [];
  let currentDay = null;
  let group = null;
  for (const a of articles) {
    if (a.d !== currentDay) {
      currentDay = a.d;
      group = el("div", { class: "day-group" }, [
        el("a", { class: "day-heading", href: `#/day/${a.d}` }, [
          el("span", { text: jpDate(a.d) }),
          el("span", { class: "dim small", text: "この日のまとめ →" }),
        ]),
      ]);
      out.push(group);
    }
    group.append(articleCard(a, termList));
  }
  return out;
}

function articleCard(a, termList) {
  const head = el("a", { class: "article-title", href: `#/day/${a.d}/${a.i}` });
  head.append(highlight(a.t, termList));

  const meta = el("div", { class: "article-meta" }, [
    a.u ? el("span", { class: "src", text: hostOf(a.u) }) : null,
    a.k ? el("span", { class: "chip chip-ioc", text: "IOC" }) : null,
    ...(a.c || []).slice(0, 4).map((cve) =>
      el("a", { class: "chip chip-cve", href: `#/news?q=${encodeURIComponent(cve)}`, text: cve })),
  ]);

  const card = el("article", { class: "article-card" }, [head, meta]);
  if (a.s) {
    const p = el("p", { class: "article-lead" });
    p.append(highlight(a.s, termList));
    card.append(p);
  }
  return card;
}

function hostOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url.slice(0, 40);
  }
}

function monthOptions(index, year) {
  const months = [...new Set(index.days
    .filter((d) => !year || d.d.startsWith(year))
    .map((d) => monthOf(d.d)))].sort().reverse();
  return [["", "すべて"], ...months.map((m) => [m, `${m.slice(0, 4)}-${m.slice(4)}`])];
}
