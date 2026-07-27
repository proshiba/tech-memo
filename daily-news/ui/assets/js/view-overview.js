// 概要。収録範囲の全体像と、直近の日への入口。

import { el, num, jpDate, isoDate, monthOf } from "./util.js";
import { loadIndex, tagLabel } from "./store.js";

export async function renderOverview(root) {
  const index = await loadIndex();
  const s = index.stats;

  const tiles = [
    { label: "収録日数", value: num(s.days), note: `${isoDate(s.first_day)} 〜 ${isoDate(s.last_day)}` },
    { label: "記事", value: num(s.articles), note: "日々のニュース要約", href: "#/news" },
    { label: "イベント", value: num(s.events), note: `${num(s.events_linked)} 件が記事に紐づく`, href: "#/events" },
    { label: "IOC", value: num(s.iocs), note: `${num(s.ioc_days)} 日分 / アクター ${num(s.actors)}・マルウェア ${num(s.malware)}`, href: "#/ioc" },
    { label: "CVE", value: num(s.cves), note: "記事本文から抽出" },
  ];

  const recent = index.days.slice(-14).reverse();

  root.replaceChildren(
    el("section", { class: "page" }, [
      el("div", { class: "page-head" }, [
        el("h1", { text: "デイリーニュース" }),
        el("p", { class: "lede", text: "日々のセキュリティニュース要約を軸に、そこから起こした構造化イベントと、一次ソースから収集した IOC。日付でたどるか、分類軸や横断検索で探す。" }),
      ]),

      el("div", { class: "tiles" }, tiles.map((t) => {
        const body = [
          el("div", { class: "tile-value", text: t.value }),
          el("div", { class: "tile-label", text: t.label }),
          el("div", { class: "tile-note", text: t.note }),
        ];
        return t.href
          ? el("a", { class: "tile", href: t.href }, body)
          : el("div", { class: "tile" }, body);
      })),

      el("div", { class: "cols" }, [
        el("div", { class: "col" }, [
          el("h2", { class: "sec-title", text: "収録の推移" }),
          heatmap(index),
        ]),
        el("div", { class: "col col-narrow" }, [
          el("h2", { class: "sec-title", text: "最近の日" }),
          el("ul", { class: "day-list" }, recent.map((d) => el("li", {}, [
            el("a", { class: "day-row", href: `#/day/${d.d}` }, [
              el("span", { class: "day-date", text: jpDate(d.d) }),
              el("span", { class: "day-counts" }, [
                el("span", { class: "chip", text: `記事 ${d.n}` }),
                d.ev ? el("span", { class: "chip chip-link", text: `イベント ${d.ev}` }) : null,
                d.ioc ? el("span", { class: "chip chip-ioc", text: `IOC ${d.ioc}` }) : null,
              ]),
            ]),
          ]))),
          el("a", { class: "btn", href: "#/news", text: "すべての記事を見る" }),
        ]),
      ]),

      el("div", { class: "cols" }, [
        el("div", { class: "col" }, [
          el("h2", { class: "sec-title", text: "イベントの種別" }),
          typeBars(index),
        ]),
        facetCard("よく出るアクター（イベント）", index.event_facets?.actor,
                  (name) => `#/events?actor=${encodeURIComponent(name)}`, "actor"),
        facetCard("よく出るマルウェア（イベント）", index.event_facets?.malware,
                  (name) => `#/events?malware=${encodeURIComponent(name)}`, "malware"),
      ]),

      el("div", { class: "cols" }, [
        facetCard("よく出る攻撃手法", index.event_facets?.attack_method,
                  (name) => `#/events?attack_method=${encodeURIComponent(name)}`, "attack_method"),
        facetCard("IOC に多いマルウェア", index.facets.malware,
                  (name) => `#/ioc?malware=${encodeURIComponent(name)}`),
        facetCard("よく言及される CVE", index.top_cves, (name) => `#/news?q=${encodeURIComponent(name)}`),
      ]),
    ]),
  );
}

function facetCard(title, pairs, href, dimension) {
  const skip = new Set(["unknown", "N/A", "not_applicable", "other"]);
  const items = (pairs || []).filter(([name]) => name && !skip.has(name)).slice(0, 18);
  return el("div", { class: "col" }, [
    el("h2", { class: "sec-title", text: title }),
    items.length
      ? el("div", { class: "chips" }, items.map(([name, count]) =>
          el("a", { class: "chip chip-link", href: href(name), title: name }, [
            el("span", { text: dimension ? tagLabel(dimension, name) : name }),
            el("b", { text: String(count) }),
          ])))
      : el("p", { class: "dim", text: "データなし" }),
  ]);
}

/** イベント種別の内訳。件数を横棒で並べる。 */
function typeBars(index) {
  const pairs = index.event_facets?.event_type || [];
  if (!pairs.length) return el("p", { class: "dim", text: "データなし" });
  const max = Math.max(...pairs.map(([, c]) => c));
  return el("div", { class: "bars" }, pairs.map(([type, count]) =>
    el("a", { class: "bar-row", href: `#/events?event_type=${encodeURIComponent(type)}` }, [
      el("span", { class: "bar-label", text: tagLabel("event_type", type) }),
      el("span", { class: "bar-track" }, [
        el("span", { class: `bar-fill pill-${type}`, style: `--w:${Math.round((count / max) * 100)}%` }),
      ]),
      el("b", { class: "bar-value", text: String(count) }),
    ])));
}

/** 月ごとの記事数を帯で出す。棒の高さで量、色の濃さで IOC の有無を示す。 */
function heatmap(index) {
  const byMonth = new Map();
  for (const d of index.days) {
    const m = monthOf(d.d);
    const slot = byMonth.get(m) || { articles: 0, iocs: 0, days: 0 };
    slot.articles += d.n;
    slot.iocs += d.ioc || 0;
    slot.days += 1;
    byMonth.set(m, slot);
  }
  const months = [...byMonth.entries()];
  const max = Math.max(1, ...months.map(([, v]) => v.articles));

  return el("div", { class: "heat" }, [
    el("div", { class: "heat-bars" }, months.map(([m, v]) => {
      const height = Math.max(3, Math.round((v.articles / max) * 100));
      return el("a", {
        class: "heat-bar" + (v.iocs ? " has-ioc" : ""),
        href: `#/news?month=${m}`,
        title: `${m.slice(0, 4)}年${+m.slice(4)}月 — 記事 ${v.articles} / ${v.days}日${v.iocs ? ` / IOC ${v.iocs}` : ""}`,
        style: `--h:${height}%`,
      }, [el("span", { class: "sr", text: `${m} 記事 ${v.articles}` })]);
    })),
    el("div", { class: "heat-axis" }, months.map(([m], i) =>
      el("span", { class: "heat-tick", text: m.endsWith("01") || i === 0 ? m.slice(0, 4) : "" }))),
    el("p", { class: "dim small", text: `月あたり最大 ${num(max)} 記事。IOC を収集済みの月は色が濃い。` }),
  ]);
}
