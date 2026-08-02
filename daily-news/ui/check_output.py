#!/usr/bin/env python3
"""生成した JSON を元データと突き合わせて、辻褄が合っているかを確かめる。

build_ui_data.py の出力が「元の Markdown / CSV から言えること」だけを言っているかを見る。
ポータル連携仕様の適合は research_bench の validate-index.py が見るので、
ここは「対応付けが正しいか」「取りこぼしが無いか」に絞る。

    python3 daily-news/ui/build_ui_data.py
    python3 daily-news/ui/check_output.py
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_ui_data as B  # noqa: E402

UI = Path(__file__).resolve().parent
problems: list[str] = []
notes: list[str] = []


def bad(msg: str) -> None:
    problems.append(msg)


def note(msg: str) -> None:
    notes.append(msg)


def load(name: str):
    path = UI / name
    if not path.exists():
        sys.exit(f"{path} がありません。先に build_ui_data.py を実行してください。")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    index = load("data/index.json")
    articles_json = load("data/articles.json")["articles"]
    iocs_json = load("data/iocs.json")
    events_json = load("data/events.json")["events"]
    search = load("api/v1/search.json")

    days = sorted((B.parse_day(p) for p in B.NEWS_DIR.rglob("*.md")), key=lambda d: d["date"])
    articles = [(d, a) for d in days for a in d["articles"]]
    by_pos = {(d["date"], a["i"]): a for d, a in articles}
    entities = {e["id"]: e for e in search["entities"]}

    # ---- 記事の数と位置
    if len(articles_json) != len(articles):
        bad(f"articles.json の件数 {len(articles_json)} が元データ {len(articles)} と違います")
    for rec in articles_json:
        art = by_pos.get((rec["d"], rec["i"]))
        if art is None:
            bad(f"articles.json に存在しない記事があります: {rec['d']}#{rec['i']}")
        elif art["title"] != rec["t"]:
            bad(f"タイトルが違います: {rec['d']}#{rec['i']}")

    # ---- IOC の収集元が「その値を実際に載せていた日の記事」を指しているか
    rows = B.load_iocs()
    events = B.load_events()
    B.link_events_to_articles(events, articles)
    B.link_iocs_to_articles(rows, articles, events)

    days_of_value: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for r in rows:
        days_of_value[(r["spec_type"], r["value"])].add(r["news_date"])

    checked = wrong_day = 0
    for ent in search["entities"]:
        if not ent["type"].startswith("ioc."):
            continue
        seen_days = days_of_value.get((ent["type"], ent["id"]), set())
        for ref in ent.get("refs", []):
            if ref["rel"] != "収集元":
                continue
            checked += 1
            target = entities.get(ref["target"])
            if target is None:
                bad(f"収集元の参照先がありません: {ent['id']} → {ref['target']}")
                continue
            day = ref["target"].removeprefix("article:").split("#")[0]
            if day not in seen_days:
                wrong_day += 1
                bad(f"収集元が収集日と合いません: {ent['id']} は {sorted(seen_days)} に収集"
                    f"／参照先は {day}")
    note(f"収集元の参照 {checked} 件を確認（収集日と合わないもの {wrong_day} 件）")

    # ---- 収集元が記事番号の既定値に張り付いていないか
    siblings: dict[str, set[str]] = collections.defaultdict(set)
    for eid in entities:
        if "#" in eid:
            family, _, idx = eid.rpartition("#")
            siblings[family].add(idx)
    spread: collections.Counter = collections.Counter()
    for ent in search["entities"]:
        for ref in ent.get("refs", []):
            if ref["rel"] != "収集元":
                continue
            family, _, idx = ref["target"].rpartition("#")
            if len(siblings.get(family, ())) >= 2:
                spread[idx] += 1
    if spread:
        top, n = spread.most_common(1)[0]
        share = n / sum(spread.values())
        note(f"収集元の記事番号は {len(spread)} 種に散っています"
             f"（最多 #{top} が {share:.0%}）")
        if len(spread) == 1:
            bad("収集元が 1 つの記事番号に固定されています（記事が選ばれていません）")

    # ---- イベントの記事対応が source_file の日と合っているか
    mismatch = 0
    for ev, rec in zip(events, events_json):
        if ev["event_key"] != rec["k"]:
            bad("events.json の並びが元データとずれています")
            break
        if rec.get("a") and rec["a"][0] != ev["source_day"]:
            mismatch += 1
    note(f"イベントの記事対応で source_file の日と違うもの {mismatch} 件"
         "（同じ URL がその日に無く、別の日に 1 件だけあった場合）")

    # ---- iocs.json の行数と article 列
    if len(iocs_json["rows"]) != len(rows):
        bad(f"iocs.json の行数 {len(iocs_json['rows'])} が元データ {len(rows)} と違います")
    col = iocs_json["columns"].index("article")
    linked = sum(1 for row in iocs_json["rows"] if row[col])
    for row in iocs_json["rows"]:
        if row[col] and (row[col][0], row[col][1]) not in by_pos:
            bad(f"iocs.json の article が存在しない記事を指しています: {row[col]}")
    note(f"iocs.json で記事に紐づいた行 {linked}/{len(rows)}")

    # ---- 目次の件数が本文と合っているか
    counts = {d["d"]: d["n"] for d in index["days"]}
    for day in days:
        if counts.get(day["date"]) != len(day["articles"]):
            bad(f"index.json の記事数が違います: {day['date']}")

    # ---- id の重複
    dupes = len(search["entities"]) - len(entities)
    if dupes:
        bad(f"search.json に id の重複が {dupes} 件あります")

    for line in notes:
        print("  ", line)
    if problems:
        print(f"\n不整合 {len(problems)} 件:")
        for line in problems[:20]:
            print("  -", line)
        if len(problems) > 20:
            print(f"  … ほか {len(problems) - 20} 件")
        return 1
    print("\n不整合なし")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
