#!/usr/bin/env python3
"""
Correlate weekly IOC CSVs with historical IOC CSVs.

Input:
  daily-news/iocs/**/YYYYMMDD.csv

Output:
  daily-news/weekly-review/YYYY/ioc-analysis/<week_label>_current_iocs.csv
  daily-news/weekly-review/YYYY/ioc-analysis/<week_label>_ioc_matches.csv
  daily-news/weekly-review/YYYY/ioc-analysis/<week_label>_ioc_summary.csv

This script does not access the network and does not modify source IOC CSV files.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit


REQUIRED_COLUMNS = [
    "ioc_type",
    "ioc_value",
    "date",
    "category",
    "actor",
    "actor_attribute",
    "malware",
    "malware_type",
    "reference",
    "description",
    "author",
    "confidence",
]


TYPE_ALIASES = {
    "ip": "ip",
    "ipv4": "ip",
    "ip_address": "ip",
    "domain": "domain",
    "url": "url",
    "file_hash_sha256": "sha256",
    "hash_sha256": "sha256",
    "sha256": "sha256",
    "file_hash_sha1": "sha1",
    "hash_sha1": "sha1",
    "sha1": "sha1",
    "file_hash_md5": "md5",
    "hash_md5": "md5",
    "md5": "md5",
    "email": "email",
    "wallet": "wallet",
    "asn": "asn",
    "cidr": "cidr",
    "filename": "filename",
    "filepath": "filepath",
    "registry_key": "registry_key",
    "mutex": "mutex",
    "user_agent": "user_agent",
}

DEFAULT_SHARED_SERVICE_HOSTS_FILE = "daily-news/scripts/ioc_shared_service_hosts.json"

@dataclass(frozen=True)
class SharedServiceHostConfig:
    exact_hosts: frozenset[str]
    suffixes: tuple[str, ...]


def normalize_host_for_compare(host: str) -> str:
    return (host or "").strip().lower().rstrip(".")


def load_shared_service_hosts(path: Path | None) -> SharedServiceHostConfig:
    if path is None:
        return SharedServiceHostConfig(exact_hosts=frozenset(), suffixes=tuple())

    if not path.exists():
        return SharedServiceHostConfig(exact_hosts=frozenset(), suffixes=tuple())

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    exact_hosts = {
        normalize_host_for_compare(h)
        for h in data.get("host_overlap_exclude_exact_hosts", [])
        if isinstance(h, str) and h.strip()
    }

    suffixes = []
    for suffix in data.get("host_overlap_exclude_suffixes", []):
        if not isinstance(suffix, str) or not suffix.strip():
            continue
        s = suffix.strip().lower()
        if not s.startswith("."):
            s = "." + s
        suffixes.append(s.rstrip("."))

    return SharedServiceHostConfig(
        exact_hosts=frozenset(exact_hosts),
        suffixes=tuple(sorted(set(suffixes))),
    )


def is_shared_service_host(host: str, config: SharedServiceHostConfig) -> bool:
    h = normalize_host_for_compare(host)
    if not h:
        return False

    if h in config.exact_hosts:
        return True

    for suffix in config.suffixes:
        # suffix is like ".github.io"
        # Match foo.github.io, but not github.io unless it is explicitly listed.
        if h.endswith(suffix):
            return True

    return False

@dataclass(frozen=True)
class IocRow:
    source_file: str
    source_line: int
    file_date: str
    row_date: str
    ioc_type: str
    ioc_value: str
    normalized_type: str
    normalized_value: str
    host: str
    category: str
    actor: str
    actor_attribute: str
    malware: str
    malware_type: str
    reference: str
    description: str
    author: str
    confidence: str


def parse_yyyy_mm_dd(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def file_date_from_name(path: Path) -> str:
    match = re.search(r"(\d{8})", path.stem)
    if not match:
        return ""
    raw = match.group(1)
    return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"


def defang_to_plain(value: str) -> str:
    v = (value or "").strip()

    replacements = {
        "hxxps://": "https://",
        "hxxp://": "http://",
        "HXXPS://": "https://",
        "HXXP://": "http://",
        "[.]": ".",
        "(.)": ".",
        "{.}": ".",
        "[:]": ":",
        "[://]": "://",
    }
    for old, new in replacements.items():
        v = v.replace(old, new)

    # Common loose defangs.
    v = re.sub(r"\[\s*\.\s*\]", ".", v)
    v = re.sub(r"\(\s*\.\s*\)", ".", v)
    v = re.sub(r"\{\s*\.\s*\}", ".", v)
    v = re.sub(r"\[\s*:\s*\]", ":", v)

    return v.strip()


def canonical_type(ioc_type: str) -> str:
    key = (ioc_type or "").strip().lower().replace("-", "_")
    return TYPE_ALIASES.get(key, key or "other")


def normalize_domain(value: str) -> tuple[str, str]:
    v = defang_to_plain(value).strip().strip("\"'").lower()

    # If a URL accidentally appears as domain, extract host.
    if "://" in v:
        parsed = urlsplit(v)
        host = parsed.hostname or ""
        return host.rstrip("."), host.rstrip(".")

    # Remove path if present.
    v = v.split("/")[0]
    v = v.rstrip(".")
    return v, v


def normalize_url(value: str) -> tuple[str, str]:
    v = defang_to_plain(value).strip().strip("\"'")

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", v):
        # Keep as-is if the source says URL but scheme is missing.
        lowered = v.lower()
        host = lowered.split("/")[0].rstrip(".")
        return lowered, host

    parsed = urlsplit(v)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    host = parsed.hostname.lower().rstrip(".") if parsed.hostname else ""

    # Remove default ports for stability.
    if parsed.port:
        default_port = (scheme == "http" and parsed.port == 80) or (scheme == "https" and parsed.port == 443)
        if default_port:
            netloc = host
        else:
            netloc = f"{host}:{parsed.port}"

    path = parsed.path or ""
    if path == "/" and not parsed.query and not parsed.fragment:
        path = ""

    normalized = urlunsplit((scheme, netloc, path, parsed.query, parsed.fragment))
    return normalized, host


def normalize_value(ioc_type: str, ioc_value: str) -> tuple[str, str, str]:
    ctype = canonical_type(ioc_type)

    if ctype == "domain":
        normalized, host = normalize_domain(ioc_value)
        return ctype, normalized, host

    if ctype == "url":
        normalized, host = normalize_url(ioc_value)
        return ctype, normalized, host

    if ctype in {"sha256", "sha1", "md5"}:
        return ctype, defang_to_plain(ioc_value).strip().lower(), ""

    if ctype == "email":
        return ctype, defang_to_plain(ioc_value).strip().lower(), ""

    if ctype == "ip":
        return ctype, defang_to_plain(ioc_value).strip(), ""

    return ctype, defang_to_plain(ioc_value).strip(), ""


def read_ioc_csv(path: Path) -> list[IocRow]:
    rows: list[IocRow] = []
    file_date = file_date_from_name(path)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return rows

        # Be tolerant of extra columns, but require the core columns.
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            raise ValueError(f"{path}: missing columns: {missing}")

        for line_no, row in enumerate(reader, start=2):
            if not row:
                continue
            if all(not (v or "").strip() for v in row.values()):
                continue

            ioc_type = (row.get("ioc_type") or "").strip()
            ioc_value = (row.get("ioc_value") or "").strip()
            if not ioc_type or not ioc_value:
                continue

            ntype, nvalue, host = normalize_value(ioc_type, ioc_value)
            if not nvalue:
                continue

            row_date = (row.get("date") or "").strip() or file_date

            rows.append(
                IocRow(
                    source_file=str(path),
                    source_line=line_no,
                    file_date=file_date,
                    row_date=row_date,
                    ioc_type=ioc_type,
                    ioc_value=ioc_value,
                    normalized_type=ntype,
                    normalized_value=nvalue,
                    host=host,
                    category=(row.get("category") or "").strip(),
                    actor=(row.get("actor") or "").strip(),
                    actor_attribute=(row.get("actor_attribute") or "").strip(),
                    malware=(row.get("malware") or "").strip(),
                    malware_type=(row.get("malware_type") or "").strip(),
                    reference=(row.get("reference") or "").strip(),
                    description=(row.get("description") or "").strip(),
                    author=(row.get("author") or "").strip(),
                    confidence=(row.get("confidence") or "").strip(),
                )
            )

    return rows


def iter_ioc_files(ioc_dir: Path) -> Iterable[Path]:
    yield from sorted(ioc_dir.glob("**/*.csv"))


def write_current_iocs(path: Path, rows: list[IocRow]) -> None:
    fieldnames = [
        "date",
        "source_file",
        "source_line",
        "ioc_type",
        "ioc_value",
        "normalized_type",
        "normalized_value",
        "host",
        "category",
        "actor",
        "actor_attribute",
        "malware",
        "malware_type",
        "reference",
        "description",
        "confidence",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "date": r.row_date,
                    "source_file": r.source_file,
                    "source_line": r.source_line,
                    "ioc_type": r.ioc_type,
                    "ioc_value": r.ioc_value,
                    "normalized_type": r.normalized_type,
                    "normalized_value": r.normalized_value,
                    "host": r.host,
                    "category": r.category,
                    "actor": r.actor,
                    "actor_attribute": r.actor_attribute,
                    "malware": r.malware,
                    "malware_type": r.malware_type,
                    "reference": r.reference,
                    "description": r.description,
                    "confidence": r.confidence,
                }
            )


def build_matches(current: list[IocRow], past: list[IocRow], include_host_overlap: bool) -> list[dict[str, str]]:
    exact_index: dict[tuple[str, str], list[IocRow]] = defaultdict(list)
    host_index: dict[str, list[IocRow]] = defaultdict(list)

    for p in past:
        exact_index[(p.normalized_type, p.normalized_value)].append(p)
        if include_host_overlap and p.host:
            host_index[p.host].append(p)

    matches: list[dict[str, str]] = []
    seen: set[tuple[str, int, str, int, str]] = set()

    for c in current:
        exact_matches = exact_index.get((c.normalized_type, c.normalized_value), [])
        for p in exact_matches:
            key = (c.source_file, c.source_line, p.source_file, p.source_line, "exact")
            if key in seen:
                continue
            seen.add(key)
            matches.append(match_record(c, p, "exact"))

        if include_host_overlap and c.host:
            for p in host_index.get(c.host, []):
                if p.normalized_type == c.normalized_type and p.normalized_value == c.normalized_value:
                    continue
                key = (c.source_file, c.source_line, p.source_file, p.source_line, "host_overlap")
                if key in seen:
                    continue
                seen.add(key)
                matches.append(match_record(c, p, "host_overlap"))

    return matches


def match_record(current: IocRow, past: IocRow, match_type: str) -> dict[str, str]:
    same_reference = "true" if current.reference and current.reference == past.reference else "false"
    same_malware = "true" if current.malware and current.malware.lower() == past.malware.lower() else "false"
    same_actor = "true" if current.actor and current.actor.lower() == past.actor.lower() else "false"

    return {
        "match_type": match_type,
        "same_reference": same_reference,
        "same_malware": same_malware,
        "same_actor": same_actor,
        "target_date": current.row_date,
        "target_source_file": current.source_file,
        "target_source_line": str(current.source_line),
        "target_ioc_type": current.ioc_type,
        "target_ioc_value": current.ioc_value,
        "target_normalized_type": current.normalized_type,
        "target_normalized_value": current.normalized_value,
        "target_host": current.host,
        "target_category": current.category,
        "target_actor": current.actor,
        "target_actor_attribute": current.actor_attribute,
        "target_malware": current.malware,
        "target_malware_type": current.malware_type,
        "target_reference": current.reference,
        "target_confidence": current.confidence,
        "past_date": past.row_date,
        "past_source_file": past.source_file,
        "past_source_line": str(past.source_line),
        "past_ioc_type": past.ioc_type,
        "past_ioc_value": past.ioc_value,
        "past_category": past.category,
        "past_actor": past.actor,
        "past_actor_attribute": past.actor_attribute,
        "past_malware": past.malware,
        "past_malware_type": past.malware_type,
        "past_reference": past.reference,
        "past_confidence": past.confidence,
        "past_description": past.description,
    }


def write_matches(path: Path, matches: list[dict[str, str]]) -> None:
    fieldnames = [
        "match_type",
        "same_reference",
        "same_malware",
        "same_actor",
        "target_date",
        "target_source_file",
        "target_source_line",
        "target_ioc_type",
        "target_ioc_value",
        "target_normalized_type",
        "target_normalized_value",
        "target_host",
        "target_category",
        "target_actor",
        "target_actor_attribute",
        "target_malware",
        "target_malware_type",
        "target_reference",
        "target_confidence",
        "past_date",
        "past_source_file",
        "past_source_line",
        "past_ioc_type",
        "past_ioc_value",
        "past_category",
        "past_actor",
        "past_actor_attribute",
        "past_malware",
        "past_malware_type",
        "past_reference",
        "past_confidence",
        "past_description",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in matches:
            writer.writerow(row)


def write_summary(path: Path, current: list[IocRow], matches: list[dict[str, str]]) -> None:
    rows: list[dict[str, str]] = []

    def add(metric: str, name: str, count: int) -> None:
        rows.append({"metric": metric, "name": name, "count": str(count)})

    current_distinct = {(r.normalized_type, r.normalized_value) for r in current}
    matched_distinct = {(m["target_normalized_type"], m["target_normalized_value"]) for m in matches}
    cross_reference_distinct = {
        (m["target_normalized_type"], m["target_normalized_value"])
        for m in matches
        if m["same_reference"] == "false"
    }

    add("target_ioc_rows", "total", len(current))
    add("target_ioc_distinct", "total", len(current_distinct))
    add("matched_ioc_rows", "total", len(matches))
    add("matched_ioc_distinct", "total", len(matched_distinct))
    add("cross_reference_matched_ioc_distinct", "total", len(cross_reference_distinct))

    for name, count in Counter(r.normalized_type for r in current).most_common():
        add("target_ioc_type", name, count)

    for name, count in Counter(r.category or "unknown" for r in current).most_common():
        add("target_category", name, count)

    for name, count in Counter(r.actor or "unknown" for r in current).most_common():
        add("target_actor", name, count)

    for name, count in Counter(r.actor_attribute or "unknown" for r in current).most_common():
        add("target_actor_attribute", name, count)

    for name, count in Counter(r.malware or "unknown" for r in current).most_common():
        add("target_malware", name, count)

    for name, count in Counter(m["match_type"] for m in matches).most_common():
        add("match_type", name, count)

    for name, count in Counter(m["target_normalized_type"] for m in matches).most_common():
        add("matched_ioc_type", name, count)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "name", "count"], lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(description="Correlate weekly IOC CSVs with historical IOC CSVs.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--ioc-dir", default="daily-news/iocs", help="IOC directory relative to repo root.")
    parser.add_argument("--target-start", required=True, help="Target week start date: YYYY-MM-DD")
    parser.add_argument("--target-end", required=True, help="Target week end date: YYYY-MM-DD")
    parser.add_argument("--week-label", required=True, help="Week label, e.g. 2026-W19")
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory. Default: daily-news/weekly-review/<year>/ioc-analysis",
    )
    parser.add_argument(
        "--include-host-overlap",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Also match URL/domain rows by host overlap. Default: true.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    ioc_dir = (repo_root / args.ioc_dir).resolve()

    target_start = parse_yyyy_mm_dd(args.target_start)
    target_end = parse_yyyy_mm_dd(args.target_end)
    if target_start is None or target_end is None:
        raise SystemExit("target-start and target-end must be YYYY-MM-DD")
    if target_end < target_start:
        raise SystemExit("target-end must be >= target-start")

    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else repo_root / "daily-news" / "weekly-review" / str(target_end.year) / "ioc-analysis"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[IocRow] = []
    for csv_path in iter_ioc_files(ioc_dir):
        all_rows.extend(read_ioc_csv(csv_path))

    current: list[IocRow] = []
    past: list[IocRow] = []

    for row in all_rows:
        row_dt = parse_yyyy_mm_dd(row.row_date)
        if row_dt is None:
            continue

        if target_start <= row_dt <= target_end:
            current.append(row)
        elif row_dt < target_start:
            past.append(row)

    current.sort(key=lambda r: (r.row_date, r.normalized_type, r.normalized_value, r.source_file, r.source_line))
    past.sort(key=lambda r: (r.row_date, r.normalized_type, r.normalized_value, r.source_file, r.source_line))

    matches = build_matches(current, past, include_host_overlap=args.include_host_overlap)
    matches.sort(
        key=lambda m: (
            m["target_date"],
            m["target_normalized_type"],
            m["target_normalized_value"],
            m["match_type"],
            m["past_date"],
            m["past_source_file"],
            m["past_source_line"],
        )
    )

    current_path = output_dir / f"{args.week_label}_current_iocs.csv"
    matches_path = output_dir / f"{args.week_label}_ioc_matches.csv"
    summary_path = output_dir / f"{args.week_label}_ioc_summary.csv"

    write_current_iocs(current_path, current)
    write_matches(matches_path, matches)
    write_summary(summary_path, current, matches)

    print(f"target_start: {args.target_start}")
    print(f"target_end: {args.target_end}")
    print(f"week_label: {args.week_label}")
    print(f"ioc_files_scanned: {len(list(iter_ioc_files(ioc_dir)))}")
    print(f"current_ioc_rows: {len(current)}")
    print(f"past_ioc_rows: {len(past)}")
    print(f"match_rows: {len(matches)}")
    print(f"current_iocs_csv: {current_path}")
    print(f"ioc_matches_csv: {matches_path}")
    print(f"ioc_summary_csv: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
