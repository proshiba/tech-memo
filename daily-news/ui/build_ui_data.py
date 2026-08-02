#!/usr/bin/env python3
"""daily-news の Markdown / CSV から、UI と research_bench ポータル用の静的 JSON を作る。

標準ライブラリだけで動く。ビルド工程は無い（UI 側もバニラ JS）。

    python3 daily-news/ui/build_ui_data.py            # daily-news/ui/{data,api} を生成
    python3 daily-news/ui/build_ui_data.py --check    # 生成せずに解析結果の統計だけ出す

出力:

    daily-news/ui/data/index.json          日付一覧・統計・ファセット
    daily-news/ui/data/articles.json       記事の軽量索引（一覧と全文検索の土台）
    daily-news/ui/data/news/<quarter>.json 四半期ごとの本文（日を開いたときに遅延ロード）
    daily-news/ui/data/iocs.json           IOC 全件（列指向の配列）
    daily-news/ui/data/events.json         構造化イベントとタグ全件
    daily-news/ui/api/v1/meta.json         ポータル連携仕様 v1
    daily-news/ui/api/v1/search.json       同上・索引本体

仕様: https://github.com/proshiba/research_bench/blob/main/docs/portal-spec.md
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NEWS_DIR = REPO / "daily-news" / "news"
IOCS_DIR = REPO / "daily-news" / "iocs"
DATA_DIR = REPO / "daily-news" / "data"
UI_DIR = Path(__file__).resolve().parent

APP_ID = "tech-memo-daily-news"
APP_NAME = "デイリーニュース"
REPOSITORY = "https://github.com/proshiba/tech-memo"
SITE_URL = "https://proshiba.github.io/tech-memo/daily-news/ui/"

# ---------------------------------------------------------------- Markdown

# 日ごとのファイルに現れる見出し。表記ゆれを 1 つのキーに寄せる。
SECTION_KEYS = {
    "tools": "tools",
    "malware campaign": "malware_campaign",
    "security report": "security_report",
    "cybercrime topics": "cybercrime",
    "日々のニュース要約": "news",
    "ニュース": "news",
    "日本のインシデント事例": "jp_incidents",
    "日本の侵害事例": "jp_incidents",
    "その他のメモ": "memo",
    "課題": "issues",
    "概要": "overview",
}

# 記事本文の中で使われるラベル付き箇条書き。
BLOCK_KEYS = {
    "要約": "summary",
    "iocの列挙": "ioc",
    "推奨事項": "advice",
    "その他": "etc",
    "chatgptの推奨事項": "gpt",
    "chatgptの推奨事項を記載": "gpt",
    "追記": "note",
    "タイトル": "title",
}

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.*)$")
NUMBERED_URL_RE = re.compile(r"^\d+\.\s+(https?://\S+)\s*$")
URL_ONLY_RE = re.compile(r"^\s*<?(https?://\S+?)>?\s*$")
CVE_RE = re.compile(r"CVE-(\d{4})-(\d{4,7})", re.I)
EMPTY_MARKERS = {"", "n/a", "na", "なし", "無し", "xxxxx", "-", "ー"}


def is_empty_section(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    return stripped.lower() in EMPTY_MARKERS


def split_sections(lines: list[str]) -> list[tuple[int, str, list[str]]]:
    """(見出しレベル, 見出し文字列, 本文行) の並びに割る。本文だけの前置きは level 0。"""
    out: list[tuple[int, str, list[str]]] = []
    cur_level, cur_title, buf = 0, "", []
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            out.append((cur_level, cur_title, buf))
            cur_level, cur_title, buf = len(m.group(1)), m.group(2), []
        else:
            buf.append(line)
    out.append((cur_level, cur_title, buf))
    return [s for s in out if s[1] or "".join(s[2]).strip()]


def normalize_label(text: str) -> tuple[str, str]:
    """`- 要約` / `- タイトル: "…"` の見出し部分と、同じ行に続く本文を返す。"""
    head, _, rest = text.partition(":")
    if "：" in head and ":" not in text:
        head, _, rest = text.partition("：")
    return head.strip().lower(), rest.strip()


def parse_blocks(body: list[str]) -> tuple[dict[str, list[list]], list[str]]:
    """記事本文を `- 要約` などのラベル単位に割る。

    各ブロックは [インデント段数, テキスト] の並びで持ち、入れ子を保つ。
    ラベルに属さない行は lead として返す。
    """
    blocks: dict[str, list[list]] = {}
    lead: list[str] = []
    current: str | None = None
    base_indent = 0

    for raw in body:
        if not raw.strip():
            continue
        m = BULLET_RE.match(raw)
        if not m:
            if current is None:
                lead.append(raw.strip())
            else:
                blocks[current].append([1, raw.strip()])
            continue

        indent = len(m.group(1).expandtabs(4))
        text = m.group(2).strip()
        label, rest = normalize_label(text)

        if label in BLOCK_KEYS and (current is None or indent <= base_indent):
            current = BLOCK_KEYS[label]
            base_indent = indent
            blocks.setdefault(current, [])
            if rest:
                blocks[current].append([1, rest.strip('"“”')])
            continue

        if current is None:
            lead.append(text)
        else:
            level = max(1, (indent - base_indent) // 4 + 1) if indent > base_indent else 1
            blocks[current].append([level, text])

    return blocks, lead


def parse_articles(body: list[str], subs: list[tuple[int, str, list[str]]]) -> list[dict]:
    """ニュース節から記事を取り出す。3 種類の書式に対応する。

    body はニュース見出し直下の本文、subs はそれに従属する下位見出しの並び。
    """
    # 書式 A/B: 従属する見出しが記事タイトル
    if subs:
        return [build_article(title, sub_body) for _, title, sub_body in subs]

    if is_empty_section("\n".join(body)):
        return []

    articles: list[dict] = []

    # 書式 C（2023 年前半）: `1. <url>` で始まり `- タイトル: "…"` を持つ
    chunks: list[tuple[str, list[str]]] = []
    cur_url, buf = None, []
    for line in body:
        m = NUMBERED_URL_RE.match(line.strip())
        if m:
            if cur_url is not None:
                chunks.append((cur_url, buf))
            cur_url, buf = m.group(1), []
        elif cur_url is not None:
            buf.append(line)
    if cur_url is not None:
        chunks.append((cur_url, buf))

    for url, chunk in chunks:
        art = build_article("", chunk)
        art["url"] = art.get("url") or url
        articles.append(art)
    return articles


def build_article(title: str, body: list[str]) -> dict:
    url = ""
    rest: list[str] = []
    for line in body:
        if not url:
            m = URL_ONLY_RE.match(line)
            if m and not BULLET_RE.match(line):
                url = m.group(1).rstrip(".,)")
                continue
        rest.append(line)

    blocks, lead = parse_blocks(rest)

    if not title:
        head = blocks.pop("title", None)
        if head:
            title = head[0][1].strip('"“”')
        elif lead:
            title = lead[0]
    else:
        blocks.pop("title", None)

    art: dict = {"title": title.strip(), "url": url}
    for key in ("summary", "ioc", "advice", "etc", "gpt", "note"):
        if blocks.get(key):
            art[key] = blocks[key]
    cves = sorted({f"CVE-{m.group(1)}-{m.group(2)}" for m in CVE_RE.finditer("\n".join(body))})
    if cves:
        art["cve"] = cves
    return art


def parse_day(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    sections = split_sections(lines)

    day: dict = {"date": path.stem, "sections": {}, "articles": []}
    for i, (level, title, body) in enumerate(sections):
        key = SECTION_KEYS.get(title.strip().lower())
        if key is None:
            continue

        # この見出しに従属する下位見出し（次の同レベル以上の見出しまで）
        subs: list[tuple[int, str, list[str]]] = []
        for sub in sections[i + 1:]:
            # 同レベル以上の見出し、または別の既知セクションが来たら終わり
            if sub[0] <= level or SECTION_KEYS.get(sub[1].strip().lower()):
                break
            subs.append(sub)

        if key == "news":
            direct = [s for s in subs if s[0] == min((x[0] for x in subs), default=0)]
            day["articles"] = parse_articles(body, direct)
            continue

        text = "\n".join(body).strip("\n")
        if subs:
            for sl, st, sb in subs:
                text += "\n" + "#" * sl + " " + st + "\n" + "\n".join(sb).strip("\n")
        text = text.strip("\n")
        if not is_empty_section(text):
            day["sections"][key] = text

    for i, art in enumerate(day["articles"]):
        art["i"] = i
    return day


# ---------------------------------------------------------------- IOC CSV

IOC_COLUMNS = [
    "ioc_type", "ioc_value", "date", "category", "actor", "actor_attribute",
    "malware", "malware_type", "reference", "description", "author", "confidence",
]

# CSV の ioc_type → 仕様 v1 の type
IOC_TYPE_MAP = {
    "domain": "ioc.domain",
    "url": "ioc.url",
    "email": "ioc.email",
    "file_hash_md5": "ioc.md5",
    "file_hash_sha1": "ioc.sha1",
    "file_hash_sha256": "ioc.sha256",
    "file_hash_sha512": "ioc.sha512",
}

IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
DEFANG_RE = re.compile(r"\[\.\]|\(\.\)|\[dot\]|\(dot\)", re.I)


def refang(value: str) -> str:
    v = DEFANG_RE.sub(".", value.strip())
    v = re.sub(r"^hxxp", "http", v, flags=re.I)
    v = v.replace("[:]", ":").replace("[@]", "@").replace("[at]", "@")
    return v.strip()


def spec_type(ioc_type: str, value: str) -> str:
    t = ioc_type.strip().lower()
    if t in IOC_TYPE_MAP:
        return IOC_TYPE_MAP[t]
    if t == "ip":
        return "ioc.ipv4" if IPV4_RE.match(value) else "ioc.ipv6"
    return "ioc.domain" if "." in value else "report"


def normalize_value(stype: str, value: str) -> str:
    v = refang(value)
    if stype in ("ioc.md5", "ioc.sha1", "ioc.sha256", "ioc.sha512", "ioc.domain",
                 "ioc.email", "ioc.endpoint"):
        v = v.lower().rstrip(".")
    elif stype == "ioc.url":
        m = re.match(r"^([A-Za-z][A-Za-z0-9+.\-]*)://(.*)$", v)
        if m:
            v = m.group(1).lower() + "://" + m.group(2)
    return v


def split_names(raw: str) -> list[str]:
    """`Vidar Stealer, XMRig` / `Macsync / Shub Stealer / AMOS` を個別の名前に割る。"""
    if not raw:
        return []
    cleaned = re.sub(r"\((?:high|medium|low)\s+confidence\)", "", raw, flags=re.I)
    parts = re.split(r"\s*[,/、]\s*|\s+または\s+", cleaned)
    out = []
    for p in parts:
        p = p.strip().strip("()")
        if not p or p.lower() in ("unknown", "n/a", "na", "none", "不明"):
            continue
        out.append(p)
    return out


def load_iocs() -> list[dict]:
    rows: list[dict] = []
    if not IOCS_DIR.exists():
        return rows
    for path in sorted(IOCS_DIR.rglob("*.csv")):
        news_date = path.stem
        with path.open(encoding="utf-8-sig", newline="") as fh:
            for rec in csv.DictReader(fh):
                value = (rec.get("ioc_value") or "").strip()
                if not value:
                    continue
                stype = spec_type(rec.get("ioc_type") or "", value)
                rec = {k: (rec.get(k) or "").strip() for k in IOC_COLUMNS}
                rec["news_date"] = news_date
                rec["spec_type"] = stype
                rec["value"] = normalize_value(stype, value)
                rows.append(rec)
    return rows


def load_ioc_logs() -> dict[str, str]:
    logs: dict[str, str] = {}
    if not IOCS_DIR.exists():
        return logs
    for path in sorted(IOCS_DIR.rglob("*.md")):
        logs[path.stem] = path.read_text(encoding="utf-8").strip()
    return logs


# ---------------------------------------------------------------- イベント CSV

# 記事本文を構造化したもの。ニュースと同じ実体を別の切り口で見るための層。
EVENT_COLUMNS = [
    "event_key", "date", "week", "month", "event_type", "title", "summary",
    "source_file", "source_url", "confidence", "needs_review", "monthly_followup_candidate",
]

CONFIDENCE_CODE = {"high": "h", "medium": "m", "low": "l"}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return [{k: (v or "").strip() for k, v in rec.items() if k} for rec in csv.DictReader(fh)]


def load_taxonomy() -> tuple[list[dict], dict[str, dict[str, str]]]:
    """次元の定義と、`normalized_value` → 日本語ラベルの対応。"""
    tax = DATA_DIR / "taxonomy"
    dimensions: list[dict] = []
    labels: dict[str, dict[str, str]] = {}

    dim_file = tax / "taxonomy_dimensions.csv"
    if dim_file.exists():
        for rec in read_csv(dim_file):
            if rec.get("active", "true").lower() == "false":
                continue
            dimensions.append({
                "key": rec["dimension"],
                "label": rec["label_ja"],
                "mode": rec["value_mode"],
                "description": rec["description"],
                "sort": int(rec["sort_order"] or 0),
            })
        dimensions.sort(key=lambda d: d["sort"])

    val_file = tax / "taxonomy_values.csv"
    if val_file.exists():
        for rec in read_csv(val_file):
            if rec.get("active", "true").lower() == "false":
                continue
            labels.setdefault(rec["dimension"], {})[rec["normalized_value"]] = rec["label_ja"]
    return dimensions, labels


def load_events() -> list[dict]:
    """イベントとタグを読む。

    月まとめの `events.csv` と日ごとの `events/<日付>.csv` が併存する時期があり、
    同じ事象が別の `event_key` で両方に入っている。日ごとのファイルがある日は
    そちらを正とし、月まとめからはその日を採らない。
    """
    if not DATA_DIR.exists():
        return []

    daily = [r for p in sorted(DATA_DIR.glob("*/*/events/*.csv")) for r in read_csv(p)]
    monthly = [r for p in sorted(DATA_DIR.glob("*/*/events.csv")) for r in read_csv(p)]
    covered = {r["date"] for r in daily}
    events = daily + [r for r in monthly if r["date"] not in covered]

    tags = [r for p in sorted(DATA_DIR.glob("*/*/event_tags/*.csv")) for r in read_csv(p)]
    tags += [r for p in sorted(DATA_DIR.glob("*/*/event_tags.csv")) for r in read_csv(p)]

    by_key: dict[str, list[list]] = collections.defaultdict(list)
    keys = {r["event_key"] for r in events}
    for t in tags:
        if t["event_key"] not in keys or not t.get("normalized_value"):
            continue
        by_key[t["event_key"]].append([
            t["dimension"],
            t["normalized_value"],
            t.get("raw_value", ""),
            CONFIDENCE_CODE.get(t.get("confidence", "").lower(), ""),
            t.get("note", ""),
        ])

    for ev in events:
        ev["tags"] = by_key.get(ev["event_key"], [])
        ev["news_date"] = ev["date"].replace("-", "")
        # どのニュースファイルから起こしたかは source_file が持っている。
        # 同じ記事 URL が複数の日に出ることがあるので、対応付けはこの日付を優先する。
        ev["source_day"] = source_file_day(ev.get("source_file", "")) or ev["news_date"]
    events.sort(key=lambda e: (e["date"], e["event_key"]))
    return events


SOURCE_FILE_DAY = re.compile(r"(\d{8})\.md$")


def source_file_day(path: str) -> str:
    m = SOURCE_FILE_DAY.search(str(path or ""))
    return m.group(1) if m else ""


# ---------------------------------------------------------------- 記事との対応付け
#
# イベントも IOC も「どの記事から起こしたか」を URL で辿る。同じ記事 URL が別の日に
# 再掲されることがあるので、まず日付を絞ってから引き、それでも複数に当たるときは
# 決められなかったものとして扱う。誤った対応は、対応が無いことより悪い。

URL_IN_TEXT = re.compile(r"(?:https?|hxxps?)://[^\s<>\"'）」,]+", re.I)

# 記事本文のうち URL が出てくるブロック。「その他」の一次ソースが主だが、
# 要約や推奨事項に直接書かれていることもある。
URL_BLOCKS = ("etc", "summary", "advice", "gpt", "note", "ioc")


def build_article_urls(articles: list) -> dict:
    """記事を URL から引くための索引。

    IOC CSV の `reference` は、ニュース記事の URL のこともあれば、その記事が挙げていた
    一次ソース（ベンダーのブログなど）のこともある。前者は見出しの URL、後者は本文中の
    URL と突き合わせれば当たる。
    """
    head: dict[tuple[str, str], set[int]] = collections.defaultdict(set)
    body: dict[tuple[str, str], set[int]] = collections.defaultdict(set)
    anywhere: dict[str, set[tuple[str, int]]] = collections.defaultdict(set)

    for day, art in articles:
        if art.get("url"):
            key = url_key(art["url"])
            head[(day["date"], key)].add(art["i"])
            anywhere[key].add((day["date"], art["i"]))
        text = "\n".join(t for block in URL_BLOCKS for _, t in art.get(block, []))
        for m in URL_IN_TEXT.finditer(text):
            body[(day["date"], url_key(m.group(0)))].add(art["i"])

    return {"head": head, "body": body, "anywhere": anywhere}


def events_by_day(events: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = collections.defaultdict(list)
    for ev in events:
        if ev.get("article"):
            out[ev["news_date"]].append(ev)
    return out


def resolve_ioc_article(row: dict, urls: dict, by_day: dict) -> tuple[tuple[str, int] | None, str]:
    """IOC 1 行がどの記事から起こされたかを決める。

    次の順で当てる。決まらなければ参照を作らない —— 誤った参照は無いことより悪い。

    1. reference が同じ日の記事の URL          （完全一致）
    2. reference が同じ日の記事本文の URL      （完全一致・一次ソース）
    3. 同じ日のイベントのタグに malware / actor 名が一致し、候補が 1 件に定まる

    別の日の記事は候補にしない。IOC はその日のニュースファイルから起こしたものなので、
    別の日の記事が出所ということはあり得ない（同じ話題を再掲しただけの他人の空似になる）。
    """
    date = row["news_date"]
    key = url_key(row["reference"])

    hit = urls["head"].get((date, key), set())
    if len(hit) == 1:
        return (date, next(iter(hit))), "記事URL"

    hit = urls["body"].get((date, key), set())
    if len(hit) == 1:
        return (date, next(iter(hit))), "本文URL"

    names = {name_key("malware", n) for n in split_names(row["malware"]) + split_names(row["actor"])}
    names.discard("")
    if names:
        candidates = set()
        for ev in by_day.get(date, []):
            tags = set()
            for dim, normalized, raw, *_ in ev["tags"]:
                if dim not in ("malware", "actor"):
                    continue
                tags.add(name_key("malware", normalized))
                if raw:
                    tags.add(name_key("malware", raw))
            if names & (tags - {""}):
                candidates.add(tuple(ev["article"]))
        if len(candidates) == 1:
            date_str, idx = next(iter(candidates))
            return (date_str, int(idx)), "イベント"

    return None, "決められない"


def link_iocs_to_articles(rows: list[dict], articles: list, events: list[dict]) -> collections.Counter:
    urls = build_article_urls(articles)
    by_day = events_by_day(events)
    stats: collections.Counter = collections.Counter()
    for row in rows:
        hit, via = resolve_ioc_article(row, urls, by_day)
        stats[via] += 1
        if hit:
            row["article"] = [hit[0], hit[1]]
    return stats


# 記事に書かれていた元表記のうち、名前として読めるもの
DISPLAY_RAW = re.compile(r"^[^。、\n]{2,30}$")


def derive_labels(events: list[dict], tax_labels: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """taxonomy に無い値（actor / malware / product などの動的な次元）の表示名を決める。

    `xmrig` より `XMRig`、`microsoft_teams` より `Microsoft Teams` の方が読めるので、
    記事に書かれていた元表記から名前らしいものを選ぶ。無ければ正規化値のまま。
    """
    raws: dict[tuple[str, str], collections.Counter] = collections.defaultdict(collections.Counter)
    for ev in events:
        for dim, normalized, raw, *_ in ev["tags"]:
            if tax_labels.get(dim, {}).get(normalized):
                continue
            if raw and DISPLAY_RAW.match(raw.strip()):
                raws[(dim, normalized)][raw.strip()] += 1

    out = {k: dict(v) for k, v in tax_labels.items()}
    for (dim, normalized), counter in raws.items():
        label, _ = pick_label(counter, set(), normalized)
        out.setdefault(dim, {})[normalized] = label
    return out


def link_events_to_articles(events: list[dict], articles: list) -> collections.Counter:
    """イベントの `source_url` を記事に突き合わせ、記事の位置を書き込む。

    イベントは記事本文から起こしたものなので大半は一致する。日本のインシデント事例や
    その他のメモから起こしたものは記事に対応が無く、その場合は日付までで留める。

    対応付けは、そのイベントを起こしたニュースファイルの日付（`source_file`）の中だけで
    探す。同じ URL の記事が別の日にあってもそれは同じ話題の再掲であって出所ではない。
    1 日の中で複数の記事が同じ URL を持つ場合も、どちらとも決められないので付けない。
    """
    urls = build_article_urls(articles)
    stats: collections.Counter = collections.Counter()

    for ev in events:
        key = url_key(ev["source_url"])
        same_day = urls["head"].get((ev["source_day"], key), set())
        if len(same_day) == 1:
            ev["article"] = [ev["source_day"], next(iter(same_day))]
            stats["同じ日の記事"] += 1
            continue
        stats["同じ日に候補が複数" if same_day else "対応なし"] += 1

    return stats


def url_key(url: str) -> str:
    return refang(str(url or "")).lower().rstrip("/")


# ---------------------------------------------------------------- 生成

def quarter_of(path: Path) -> str:
    return path.parent.name


def write_json(path: Path, payload, *, compact: bool = True) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    sep = (",", ":") if compact else (", ", ": ")
    text = json.dumps(payload, ensure_ascii=False, separators=sep)
    if not compact:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")
    return len(text.encode("utf-8"))


def first_line(art: dict) -> str:
    for key in ("summary", "gpt", "advice"):
        block = art.get(key)
        if block:
            return block[0][1][:80]
    return ""


def build(check_only: bool = False) -> int:
    news_files = sorted(NEWS_DIR.rglob("*.md"))
    if not news_files:
        print(f"ニュースファイルが見つかりません: {NEWS_DIR}", file=sys.stderr)
        return 1

    ioc_rows = load_iocs()
    ioc_logs = load_ioc_logs()
    ioc_by_day = collections.Counter(r["news_date"] for r in ioc_rows)
    dimensions, tax_labels = load_taxonomy()
    events = load_events()
    tax_labels = derive_labels(events, tax_labels)

    quarters: dict[str, list[dict]] = collections.defaultdict(list)
    for path in news_files:
        day = parse_day(path)
        day["quarter"] = quarter_of(path)
        if day["date"] in ioc_logs:
            day["ioc_log"] = ioc_logs[day["date"]]
        quarters[day["quarter"]].append(day)

    all_days = [d for q in quarters.values() for d in q]
    all_days.sort(key=lambda d: d["date"])
    articles = [(d, a) for d in all_days for a in d["articles"]]

    # ---- 記事の軽量索引（一覧・検索用）
    article_index = []
    article_pos: dict[tuple[str, int], int] = {}
    for day, art in articles:
        article_pos[(day["date"], art["i"])] = len(article_index)
        rec = {
            "d": day["date"],
            "i": art["i"],
            "q": day["quarter"],
            "t": art["title"],
        }
        if art.get("url"):
            rec["u"] = art["url"]
        lead = first_line(art)
        if lead:
            rec["s"] = lead
        if art.get("cve"):
            rec["c"] = art["cve"]
        if art.get("ioc") and not _is_no_ioc(art["ioc"]):
            rec["k"] = 1
        article_index.append(rec)

    # 記事 ↔ イベントの対応を索引にも載せ、ニュース一覧をイベント種別で絞れるようにする
    for ev in events:
        if ev.get("article"):
            pos = article_pos.get(tuple(ev["article"]))
            if pos is not None:
                article_index[pos]["ev"] = ev["event_type"]

    event_link_stats = link_events_to_articles(events, articles)
    event_by_day = collections.Counter(e["news_date"] for e in events)
    ioc_link_stats = link_iocs_to_articles(ioc_rows, articles, events)

    # ---- 日ごとの目次
    day_index = []
    for day in all_days:
        rec = {"d": day["date"], "q": day["quarter"], "n": len(day["articles"])}
        if ioc_by_day.get(day["date"]):
            rec["ioc"] = ioc_by_day[day["date"]]
        if event_by_day.get(day["date"]):
            rec["ev"] = event_by_day[day["date"]]
        extras = [k for k in ("tools", "malware_campaign", "security_report",
                              "cybercrime", "jp_incidents", "memo") if day["sections"].get(k)]
        if extras:
            rec["x"] = extras
        day_index.append(rec)

    # ---- IOC のファセット
    facet = {
        "type": collections.Counter(),
        "category": collections.Counter(),
        "actor": collections.Counter(),
        "malware": collections.Counter(),
    }
    for r in ioc_rows:
        facet["type"][r["spec_type"]] += 1
        facet["category"][r["category"] or "unknown"] += 1
        for a in split_names(r["actor"]) or ["unknown"]:
            facet["actor"][a] += 1
        for m in split_names(r["malware"]) or ["unknown"]:
            facet["malware"][m] += 1

    cve_counter = collections.Counter(c for _, a in articles for c in a.get("cve", []))

    # ---- イベントのファセット（次元ごとの値の出現数）
    event_facets: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    event_facets["event_type"].update(e["event_type"] for e in events if e["event_type"])
    for ev in events:
        for dim, normalized, *_ in ev["tags"]:
            event_facets[dim][normalized] += 1

    # 動的な次元は表記ゆれ（teampcp / team_pcp）が残るので、英数字だけにして畳む。
    # 絞り込み側も同じ潰し方で突き合わせる（view-events.js の squash）。
    dynamic_dims = {d["key"] for d in dimensions if d["mode"] == "dynamic"}
    for dim in list(event_facets):
        if dim not in dynamic_dims:
            continue
        groups: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        for value, count in event_facets[dim].items():
            groups[NAME_STRIP.sub("", value.lower()) or value][value] += count
        merged = collections.Counter()
        for counter in groups.values():
            merged[counter.most_common(1)[0][0]] = sum(counter.values())
        event_facets[dim] = merged

    index = {
        "spec_version": "1.0",
        "app_id": APP_ID,
        "generated_at": now_iso(),
        "quarters": [
            {
                "id": q,
                "days": len(days),
                "articles": sum(len(d["articles"]) for d in days),
                "from": min(d["date"] for d in days),
                "to": max(d["date"] for d in days),
            }
            for q, days in sorted(quarters.items())
        ],
        "days": day_index,
        "stats": {
            "days": len(all_days),
            "articles": len(articles),
            "iocs": len(ioc_rows),
            "ioc_days": len(ioc_by_day),
            "cves": len(cve_counter),
            "actors": len([k for k in facet["actor"] if k != "unknown"]),
            "malware": len([k for k in facet["malware"] if k != "unknown"]),
            "events": len(events),
            "event_days": len(event_by_day),
            "events_linked": sum(1 for e in events if e.get("article")),
            "first_day": all_days[0]["date"],
            "last_day": all_days[-1]["date"],
            "first_event": events[0]["date"] if events else "",
            "last_event": events[-1]["date"] if events else "",
        },
        "facets": {k: sorted(v.items(), key=lambda kv: (-kv[1], kv[0])) for k, v in facet.items()},
        "top_cves": cve_counter.most_common(40),
        "dimensions": dimensions,
        "event_facets": {
            k: sorted(v.items(), key=lambda kv: (-kv[1], kv[0]))
            for k, v in event_facets.items()
        },
        "labels": {k: v for k, v in tax_labels.items() if k in event_facets},
    }

    if check_only:
        report(index, articles, ioc_rows, events, ioc_link_stats, event_link_stats)
        return 0

    data_dir = UI_DIR / "data"
    total = 0
    total += write_json(data_dir / "index.json", index)
    total += write_json(data_dir / "articles.json",
                        {"generated_at": index["generated_at"], "articles": article_index})
    for q, days in sorted(quarters.items()):
        total += write_json(data_dir / "news" / f"{q}.json",
                            {"quarter": q, "days": sorted(days, key=lambda d: d["date"])})
    total += write_json(data_dir / "iocs.json", {
        "generated_at": index["generated_at"],
        "columns": ["type", "value", "date", "category", "actor", "actor_attribute",
                    "malware", "malware_type", "reference", "description",
                    "confidence", "news_date", "article"],
        "rows": [
            [r["spec_type"], r["value"], r["date"], r["category"], r["actor"],
             r["actor_attribute"], r["malware"], r["malware_type"], r["reference"],
             r["description"], r["confidence"], r["news_date"], r.get("article")]
            for r in ioc_rows
        ],
    })

    total += write_json(data_dir / "events.json", {
        "generated_at": index["generated_at"],
        "events": [
            {
                "k": e["event_key"],
                "d": e["news_date"],
                "w": e["week"],
                "e": e["event_type"],
                "t": e["title"],
                "s": e["summary"],
                "u": e["source_url"],
                "c": CONFIDENCE_CODE.get(e["confidence"].lower(), ""),
                **({"a": e["article"]} if e.get("article") else {}),
                **({"r": 1} if e["needs_review"].lower() == "true" else {}),
                **({"f": e["monthly_followup_candidate"]}
                   if e["monthly_followup_candidate"] in ("yes", "maybe") else {}),
                **({"g": e["tags"]} if e["tags"] else {}),
            }
            for e in events
        ],
    })

    meta, search = build_portal_index(index, articles, ioc_rows, events)
    api_dir = UI_DIR / "api" / "v1"
    total += write_json(api_dir / "meta.json", meta, compact=False)
    search_bytes = write_json(api_dir / "search.json", search)
    total += search_bytes

    check_source_refs(search["entities"])

    st = index["stats"]
    print(f"日数 {st['days']} / 記事 {st['articles']} / IOC {st['iocs']} / "
          f"CVE {st['cves']} / イベント {st['events']}（記事に紐づく {st['events_linked']}）")
    linked = st["iocs"] - ioc_link_stats["決められない"]
    print(f"IOC の収集元 {linked}/{st['iocs']} 件を特定 "
          + " / ".join(f"{k} {v}" for k, v in ioc_link_stats.most_common()))
    print(f"イベントの記事対応 {st['events_linked']}/{st['events']} 件 "
          + " / ".join(f"{k} {v}" for k, v in event_link_stats.most_common()))
    print(f"ポータル索引 {len(search['entities'])} エンティティ "
          f"({search_bytes / 1e6:.2f} MB) / 出力合計 {total / 1e6:.2f} MB")
    return 0


def _is_no_ioc(block: list[list]) -> bool:
    joined = " ".join(t for _, t in block)
    return ("IOC情報なし" in joined or "情報なし" in joined) and len(block) <= 2


def now_iso() -> str:
    stamp = os.environ.get("SOURCE_DATE_EPOCH")
    if stamp and stamp.isdigit():
        return datetime.fromtimestamp(int(stamp), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- ポータル索引

# エンティティの補足に出すイベントの分類軸（イベント種別は別に出す）
EVENT_ATTR_DIMS = ("initial_access", "actor", "actor_attribution", "malware",
                   "product", "product_class", "attack_method", "crime_trend")

# ポータルからの deep link。type ごとにこの UI のどの画面へ入るかを決める。
DEEP_LINKS = {
    "report": "#/day/{detail}",
    "cve": "#/news?q={detail}",
    "malware": "#/events?malware={detail}",
    "actor": "#/events?actor={detail}",
    "product": "#/events?product={detail}",
    **{t: "#/ioc?q={detail}" for t in (
        "ioc.ipv4", "ioc.ipv6", "ioc.domain", "ioc.url", "ioc.endpoint",
        "ioc.email", "ioc.md5", "ioc.sha1", "ioc.sha256", "ioc.sha512")},
}


def event_attrs(ev: dict, dim_label: dict, labels: dict) -> dict:
    """イベントの構造化タグを、そのままエンティティの補足として出す。"""
    out = {}
    if ev["event_type"]:
        out["イベント種別"] = labels.get("event_type", {}).get(ev["event_type"], ev["event_type"])
    for dim in EVENT_ATTR_DIMS:
        values = [t[1] for t in ev["tags"] if t[0] == dim]
        if values:
            out[dim_label.get(dim, dim)] = join_capped(
                [labels.get(dim, {}).get(v, v) for v in values], 4)
    return out


def report_entities(articles: list, events: list[dict], dim_label: dict,
                    labels: dict) -> tuple[dict, list[dict]]:
    """記事 1 件 = report。対応するイベントがあれば構造化タグを添える。

    記事に対応が付かなかったイベント（日本のインシデント事例など、元が記事節でないもの）も
    report として出す。そうしないとイベントのタグから辿る先が無くなる。
    """
    event_of_article = {tuple(e["article"]): e for e in events if e.get("article")}
    article_id: dict[tuple[str, int], str] = {}
    out: list[dict] = []

    for day, art in articles:
        eid = f"article:{day['date']}#{art['i']}"
        article_id[(day["date"], art["i"])] = eid
        attrs = {"日付": iso_date(day["date"])}
        if art.get("cve"):
            attrs["CVE"] = join_capped(art["cve"], 6)
        ev = event_of_article.get((day["date"], art["i"]))
        if ev:
            attrs.update(event_attrs(ev, dim_label, labels))
        out.append({
            "type": "report",
            "id": eid,
            "label": art["title"] or art.get("url", "")[:80],
            "value": refang(art["url"]) if art.get("url") else f"{day['date']}#{art['i']}",
            "detail": f"{day['date']}/{art['i']}",
            "attrs": attrs,
        })

    for ev in events:
        if ev.get("article"):
            continue
        out.append({
            "type": "report",
            "id": f"event:{ev['event_key']}",
            "label": ev["title"],
            "value": refang(ev["source_url"]) or ev["event_key"],
            "detail": ev["news_date"],
            "attrs": {"日付": ev["date"], **event_attrs(ev, dim_label, labels)},
        })

    return article_id, out


def cve_entities(articles: list, article_id: dict) -> list[dict]:
    """記事本文から拾った脆弱性識別子。"""
    refs_of: dict[str, list[str]] = collections.defaultdict(list)
    for day, art in articles:
        for cve in art.get("cve", []):
            refs_of[cve].append(article_id[(day["date"], art["i"])])
    return [
        {
            "type": "cve",
            "id": cve,
            "label": cve,
            "attrs": {"言及記事数": str(len(refs))},   # refs は 12 件で打ち切るので実数はここ
            "refs": [{"rel": "言及記事", "target": t} for t in refs[:12]],
        }
        for cve, refs in sorted(refs_of.items())
    ]


def group_iocs(ioc_rows: list[dict]) -> dict[tuple[str, str], dict]:
    """同じ値の IOC を 1 件に畳む。属性は行をまたいで集める。"""
    by_value: dict[tuple[str, str], dict] = {}
    for r in ioc_rows:
        slot = by_value.setdefault((r["spec_type"], r["value"]), {
            "type": r["spec_type"], "value": r["value"],
            "categories": set(), "actors": set(), "malware": set(), "articles": set(),
            "dates": set(), "news_dates": set(), "desc": "",
        })
        if len(r["description"]) > len(slot["desc"]):
            slot["desc"] = r["description"]   # いちばん情報量のある説明を採る
        if r["category"]:
            slot["categories"].add(r["category"])
        slot["actors"].update(split_names(r["actor"]))
        slot["malware"].update(split_names(r["malware"]))
        if r.get("article"):
            slot["articles"].add(tuple(r["article"]))
        if r["date"]:
            slot["dates"].add(r["date"])
        slot["news_dates"].add(r["news_date"])
    return by_value


def ioc_entities(by_value: dict, article_id: dict) -> list[dict]:
    out = []
    for (stype, value), slot in by_value.items():
        attrs = {}
        if slot["categories"]:
            attrs["分類"] = ", ".join(sorted(slot["categories"]))
        if slot["actors"]:
            attrs["アクター"] = join_capped(sorted(slot["actors"]), 5)
        if slot["malware"]:
            attrs["マルウェア"] = join_capped(sorted(slot["malware"]), 5)
        if slot["dates"]:
            attrs["観測日"] = min(slot["dates"])
        attrs["収集日"] = join_capped(sorted(iso_date(d) for d in slot["news_dates"]), 2)
        if slot["desc"]:
            attrs["説明"] = slot["desc"][:110]

        # 収集元は「その IOC を実際に載せていた記事」だけを指す。
        # どの記事か決められなかった行は参照を作らない（誤った参照は無いことより悪い）。
        refs = [
            {"rel": "収集元", "target": article_id[key]}
            for key in sorted(slot["articles"])
            if key in article_id
        ]
        if len(refs) > 6:
            attrs["収集元の記事数"] = str(len(refs))

        out.append({
            "type": stype,
            "id": value,
            "label": value,
            "attrs": attrs,
            **({"refs": refs[:6]} if refs else {}),
        })
    return out


def name_entities(by_value: dict, events: list[dict], article_id: dict) -> tuple[dict, list[dict]]:
    """malware / actor / product を、IOC の属性とイベントのタグの両方から起こす。

    同じ名前は 1 エンティティに畳み、別表記は aliases に載せて結合キーを増やす。
    """
    registry: dict[tuple[str, str], dict] = {}

    def touch(kind: str, name: str, ref: dict | None, origin: str, alias: str = "") -> None:
        key = name_key(kind, name)
        if not key:
            return
        slot = registry.setdefault((kind, key), {
            "names": collections.Counter(), "aliases": set(), "refs": [], "ioc": 0, "event": 0,
        })
        slot["names"][name] += 1
        slot[origin] += 1
        if alias and alias != name:
            slot["aliases"].add(alias)
        if ref and len(slot["refs"]) < 24 and ref not in slot["refs"]:
            slot["refs"].append(ref)

    for (stype, value), slot in by_value.items():
        ref = {"rel": "関連IOC", "target": value}
        for name in slot["malware"]:
            touch("malware", name, ref, "ioc")
        for name in slot["actors"]:
            touch("actor", name, ref, "ioc")

    # イベントのタグは正規化値を軸にし、記事に書かれていた元表記を別名として残す。
    for ev in events:
        target = (article_id.get(tuple(ev["article"])) if ev.get("article")
                  else f"event:{ev['event_key']}")
        ref = {"rel": "関連イベント", "target": target}
        for dim in ("malware", "actor", "product"):
            for tag in ev["tags"]:
                if tag[0] == dim:
                    touch(dim, tag[1], ref, "event", alias=tag[2])

    out = []
    for (kind, key), slot in sorted(registry.items()):
        label, aliases = pick_label(slot["names"], slot["aliases"], key)
        attrs = {}
        if slot["ioc"]:
            attrs["IOC件数"] = str(slot["ioc"])
        if slot["event"]:
            attrs["イベント件数"] = str(slot["event"])
        out.append({
            "type": kind,
            "id": f"{kind}:{key}",
            "label": label,
            "value": label,
            "detail": label,
            **({"aliases": aliases} if aliases else {}),
            "attrs": attrs,
            **({"refs": slot["refs"]} if slot["refs"] else {}),
        })
    return registry, out


def build_portal_index(index: dict, articles: list, ioc_rows: list[dict],
                       events: list[dict]) -> tuple[dict, dict]:
    """ポータル連携仕様 v1 の meta.json / search.json を組み立てる。"""
    dim_label = {d["key"]: d["label"] for d in index["dimensions"]}
    labels = index["labels"]

    article_id, entities = report_entities(articles, events, dim_label, labels)
    entities += cve_entities(articles, article_id)

    by_value = group_iocs(ioc_rows)
    entities += ioc_entities(by_value, article_id)

    registry, name_ents = name_entities(by_value, events, article_id)
    entities += name_ents

    stats = index["stats"]
    meta = {
        "spec_version": "1.0",
        "app_id": APP_ID,
        "name": APP_NAME,
        "description": "日々のセキュリティニュース要約と、そこから起こした構造化イベント・IOC の索引。",
        "generated_at": index["generated_at"],
        "repository": REPOSITORY,
        "site_url": SITE_URL,
        "endpoints": {"search": "api/v1/search.json"},
        "deep_links": dict(DEEP_LINKS),
        # embed_css は置かない。?embed=1 と iframe 判定を自前で解釈して
        # クロームを畳むため（仕様 §4 でいう embed-mode）。
        "capabilities": ["iframe", "deep-link", "embed-mode"],
        "stats": {
            "report": stats["articles"] + (stats["events"] - stats["events_linked"]),
            "ioc": len(by_value),
            "cve": stats["cves"],
            "malware": sum(1 for k, _ in registry if k == "malware"),
            "actor": sum(1 for k, _ in registry if k == "actor"),
            "product": sum(1 for k, _ in registry if k == "product"),
        },
    }
    search = {
        "spec_version": "1.0",
        "app_id": APP_ID,
        "generated_at": index["generated_at"],
        "entities": entities,
    }
    return meta, search


NAME_STRIP = re.compile(r"[^a-z0-9]+")
ASCII_NAME = re.compile(r"^[\x20-\x7e]{2,48}$")
NAME_NOISE = {"unknown", "n/a", "na", "none", "not_applicable", "不明", "該当なし", "なし"}


def name_key(kind: str, name: str) -> str:
    """エンティティをまとめる鍵。ポータルの結合キーの作り方に合わせる。

    actor / malware は英数字以外を落とすので、`lazarus_group` と `Lazarus Group` が
    同じ鍵になる。日本語だけの名前は鍵が空になり結合できないため採らない。
    product は小文字化だけなので日本語の製品名もそのまま鍵になる。
    """
    v = str(name or "").strip().lower()
    if not v or v in NAME_NOISE:
        return ""
    if kind == "product":
        return re.sub(r"\s+", " ", v)
    return NAME_STRIP.sub("", v)


def pick_label(names: collections.Counter, aliases: set, fallback: str) -> tuple[str, list[str]]:
    """表示名と別名を選ぶ。読める表記（ASCII・下線なし・多数派）を優先する。"""
    candidates = list(names) + [a for a in aliases if a not in names]
    if not candidates:
        return fallback, []
    label = min(candidates, key=lambda n: (
        0 if ASCII_NAME.match(n) else 1,
        1 if "_" in n else 0,
        -names.get(n, 0),
        n,
    ))
    alias_list = sorted({n for n in candidates if n != label and len(n) <= 60})
    return label, alias_list[:8]


def join_capped(values, limit: int, sep: str = ", ") -> str:
    """並べて表示する。入り切らない分は件数で示す（黙って切らない）。"""
    items = list(values)
    head = sep.join(items[:limit])
    rest = len(items) - limit
    return f"{head} ほか{rest}件" if rest > 0 else head


def iso_date(yyyymmdd: str) -> str:
    if len(yyyymmdd) == 8 and yyyymmdd.isdigit():
        return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"
    return yyyymmdd


def check_source_refs(entities: list[dict]) -> None:
    """`収集元` が記事番号の既定値に張り付いていないか確かめる。

    以前ここは「その日の 1 本目の記事」を無条件に指していて、ほとんどの参照が誤っていた。
    同じ不具合が黙って戻らないよう、生成の時点で落とす。
    """
    by_family: dict[str, set[str]] = collections.defaultdict(set)
    for ent in entities:
        eid = str(ent.get("id", ""))
        if "#" in eid:
            family, _, idx = eid.rpartition("#")
            by_family[family].add(idx)

    targets: collections.Counter = collections.Counter()
    total = 0
    for ent in entities:
        for ref in ent.get("refs", []):
            if ref.get("rel") != "収集元":
                continue
            family, _, idx = str(ref.get("target", "")).rpartition("#")
            if not idx or len(by_family.get(family, ())) < 2:
                continue  # 兄弟が居ない日は選びようがないので数えない
            targets[idx] += 1
            total += 1

    if total >= 50 and len(targets) == 1:
        raise SystemExit(
            f"収集元の参照 {total} 件が全て `#{next(iter(targets))}` を指しています。"
            " 記事が選ばれていません（既定値のまま出ている疑い）。",
        )


def report(index: dict, articles: list, ioc_rows: list[dict], events: list[dict],
           ioc_link_stats: collections.Counter, event_link_stats: collections.Counter) -> None:
    s = index["stats"]
    print(f"日数        {s['days']}  ({s['first_day']} 〜 {s['last_day']})")
    print(f"記事        {s['articles']}")
    print(f"IOC         {s['iocs']}  ({s['ioc_days']} 日分)")
    print(f"CVE         {s['cves']}")
    print(f"イベント     {s['events']}  ({s['first_event']} 〜 {s['last_event']}, "
          f"{s['event_days']} 日分 / 記事に紐づく {s['events_linked']})")
    print("IOC の収集元の特定:")
    for via, n in ioc_link_stats.most_common():
        print(f"  {via:<14} {n:>5}  ({n * 100 // max(1, len(ioc_rows))}%)")
    print("イベントの記事対応:")
    for via, n in event_link_stats.most_common():
        print(f"  {via:<14} {n:>5}")
    no_tag = [e for e in events if not e["tags"]]
    print(f"タグ無しイベント {len(no_tag)}")
    for e in no_tag[:3]:
        print("  タグ無し:", e["date"], e["title"][:50])
    no_title = [a for _, a in articles if not a["title"]]
    no_url = [a for _, a in articles if not a.get("url")]
    no_summary = [a for _, a in articles if not a.get("summary")]
    print(f"タイトル無し {len(no_title)} / URL 無し {len(no_url)} / 要約無し {len(no_summary)}")
    for a in no_title[:5]:
        print("  タイトル無し:", a.get("url", "")[:90])
    for a in no_summary[:5]:
        print("  要約無し:", (a["title"] or a.get("url", ""))[:70])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="生成せず統計だけ出す")
    args = ap.parse_args()
    return build(check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
