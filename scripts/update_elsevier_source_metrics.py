#!/usr/bin/env python3
"""Fetch Elsevier/Scopus source metrics by ISSN.

Inputs:
- _bibliography/publications.bib
- ELSEVIER_API_KEY environment variable
- Optional: ELSEVIER_INSTTOKEN environment variable

Outputs:
- _data/elsevier_source_metrics.json
- _data/publication_metrics.json

This script queries the Elsevier Serial Title API by ISSN and stores
journal/source-level metrics for Jekyll.

It does not modify the BibTeX file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


SERIAL_TITLE_API = "https://api.elsevier.com/content/serial/title/issn/{issn}"


def utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )


def normalize_issn(value: str | None) -> str:
    if not value:
        return ""

    value = value.strip()
    value = value.replace("{", "").replace("}", "")
    value = value.replace("ISSN", "")
    value = value.replace("issn", "")

    characters = [
        character.upper()
        for character in value
        if character.isdigit() or character.upper() == "X"
    ]

    if len(characters) != 8:
        return ""

    return "".join(characters[:4]) + "-" + "".join(characters[4:])


def split_bibtex_entries(text: str) -> list[str]:
    entries: list[str] = []
    index = 0

    while True:
        start = text.find("@", index)

        if start == -1:
            break

        opening_brace = text.find("{", start)

        if opening_brace == -1:
            break

        depth = 0
        position = opening_brace

        while position < len(text):
            character = text[position]

            if character == "{":
                depth += 1

            elif character == "}":
                depth -= 1

                if depth == 0:
                    entries.append(text[start : position + 1])
                    index = position + 1
                    break

            position += 1

        else:
            break

    return entries


def bibtex_key(entry: str) -> str | None:
    match = re.match(
        r"@\w+\s*\{\s*([^,\s]+)",
        entry,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(1)


def bibtex_type(entry: str) -> str | None:
    match = re.match(
        r"@(\w+)\s*\{",
        entry,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(1).lower()


def extract_bibtex_field(
    entry: str,
    field_name: str,
) -> str | None:
    match = re.search(
        rf"(?im)^\s*{re.escape(field_name)}\s*=\s*",
        entry,
    )

    if not match:
        return None

    position = match.end()

    while position < len(entry) and entry[position].isspace():
        position += 1

    if position >= len(entry):
        return None

    opener = entry[position]

    if opener == "{":
        depth = 0
        start = position + 1
        position += 1

        while position < len(entry):
            character = entry[position]

            if character == "{":
                depth += 1

            elif character == "}":
                if depth == 0:
                    return entry[start:position].strip()

                depth -= 1

            position += 1

    if opener == '"':
        start = position + 1
        position += 1

        while position < len(entry):
            character = entry[position]

            if character == '"' and entry[position - 1] != "\\":
                return entry[start:position].strip()

            position += 1

    start = position

    while position < len(entry) and entry[position] not in ",\n":
        position += 1

    return entry[start:position].strip()


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.replace("{", "").replace("}", "")
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def load_bibtex_publications(
    bibliography_path: Path,
) -> list[dict[str, Any]]:
    text = bibliography_path.read_text(encoding="utf-8")

    publications: list[dict[str, Any]] = []

    for entry in split_bibtex_entries(text):
        key = bibtex_key(entry)

        if not key:
            continue

        issn = normalize_issn(
            extract_bibtex_field(entry, "issn")
        )

        print_issn = normalize_issn(
            extract_bibtex_field(entry, "print_issn")
        )

        all_issns = []

        for candidate in [issn, print_issn]:
            if candidate and candidate not in all_issns:
                all_issns.append(candidate)

        publications.append(
            {
                "key": key,
                "type": bibtex_type(entry),
                "title": normalize_text(
                    extract_bibtex_field(entry, "title")
                ),
                "year": normalize_text(
                    extract_bibtex_field(entry, "year")
                ),
                "journal": normalize_text(
                    extract_bibtex_field(entry, "journal")
                ),
                "booktitle": normalize_text(
                    extract_bibtex_field(entry, "booktitle")
                ),
                "issn": issn,
                "print_issn": print_issn,
                "all_issns": all_issns,
            }
        )

    return publications


def iter_nested_values(value: Any) -> list[Any]:
    output: list[Any] = []

    def visit(item: Any) -> None:
        output.append(item)

        if isinstance(item, dict):
            for child in item.values():
                visit(child)

        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)

    return output


def find_first_key(
    payload: Any,
    possible_keys: list[str],
) -> Any:
    possible = {
        key.lower()
        for key in possible_keys
    }

    for item in iter_nested_values(payload):
        if not isinstance(item, dict):
            continue

        for key, value in item.items():
            if key.lower() in possible:
                return value

    return None


def text_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, int | float):
        return str(value)

    if isinstance(value, dict):
        for key in [
            "$",
            "_",
            "value",
            "@value",
            "#text",
            "text",
        ]:
            if key in value:
                return text_value(value[key])

    return ""


def extract_year_value_list(
    payload: Any,
    list_names: list[str],
    item_names: list[str],
) -> list[dict[str, str]]:
    """Extract values like SJRList/SJR[@year].

    Elsevier JSON can vary by view and endpoint form. This function accepts
    common JSON translations of XML such as:
    - {"SJRList": {"SJR": [{"@year": "2023", "$": "1.234"}]}}
    - {"SJRList": [{"SJR": {...}}]}
    """

    list_names_lower = {
        name.lower()
        for name in list_names
    }

    item_names_lower = {
        name.lower()
        for name in item_names
    }

    results: list[dict[str, str]] = []

    for node in iter_nested_values(payload):
        if not isinstance(node, dict):
            continue

        for key, value in node.items():
            if key.lower() not in list_names_lower:
                continue

            for child in iter_nested_values(value):
                if not isinstance(child, dict):
                    continue

                for child_key, child_value in child.items():
                    if child_key.lower() not in item_names_lower:
                        continue

                    items = child_value

                    if not isinstance(items, list):
                        items = [items]

                    for item in items:
                        if isinstance(item, dict):
                            year = text_value(
                                item.get("@year")
                                or item.get("year")
                            )
                            metric_value = text_value(item)

                            if year or metric_value:
                                results.append(
                                    {
                                        "year": year,
                                        "value": metric_value,
                                    }
                                )

                        else:
                            value_text = text_value(item)

                            if value_text:
                                results.append(
                                    {
                                        "year": "",
                                        "value": value_text,
                                    }
                                )

    return results


def latest_metric(
    values: list[dict[str, str]],
) -> dict[str, str]:
    clean_values = [
        item
        for item in values
        if item.get("value")
    ]

    if not clean_values:
        return {
            "year": "",
            "value": "",
        }

    def sort_key(item: dict[str, str]) -> int:
        try:
            return int(item.get("year") or -1)
        except ValueError:
            return -1

    return sorted(
        clean_values,
        key=sort_key,
        reverse=True,
    )[0]


def percentile_to_quartile(value: str) -> str:
    """Convert CiteScore percentile to CiteScore quartile.

    Elsevier/Scopus convention:
    - Q1: 75th–99th percentile
    - Q2: 50th–74th percentile
    - Q3: 25th–49th percentile
    - Q4: 0th–24th percentile
    """

    if value is None:
        return ""

    text = str(value).strip()

    if not text:
        return ""

    text = text.replace("%", "").replace(",", ".")

    match = re.search(r"\d+(\.\d+)?", text)

    if not match:
        return ""

    try:
        percentile = float(match.group(0))
    except ValueError:
        return ""

    # Defensive handling in case an API ever returns 0–1 instead of 0–100.
    if 0 <= percentile <= 1:
        percentile = percentile * 100

    if percentile < 0 or percentile > 100:
        return ""

    if percentile < 25:
        return "Q4"

    if percentile < 50:
        return "Q3"

    if percentile < 75:
        return "Q2"

    return "Q1"


def extract_citescore_records(payload: Any) -> list[dict[str, str]]:
    """Extract CiteScore records from Elsevier Serial Title JSON.

    This version avoids mistaking the metric year for the CiteScore value
    and extracts the best available percentile from nested subject-rank data.
    """

    def compact_key(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.lower())

    def first_value_by_keys(
        node: dict[str, Any],
        possible_keys: set[str],
    ) -> str:
        for key, value in node.items():
            if compact_key(key) in possible_keys:
                return text_value(value)
        return ""

    def looks_like_year(value: str) -> bool:
        return bool(re.fullmatch(r"20\d{2}", value.strip()))

    def looks_numeric(value: str) -> bool:
        return bool(re.fullmatch(r"\d+(\.\d+)?", value.strip()))

    def collect_rank_records(node: Any) -> list[dict[str, str]]:
        rank_records: list[dict[str, str]] = []

        for child in iter_nested_values(node):
            if not isinstance(child, dict):
                continue

            keys = {
                compact_key(key): key
                for key in child.keys()
            }

            has_rank_context = any(
                key in keys
                for key in {
                    "rank",
                    "rankoutof",
                    "percentile",
                    "citescorerank",
                    "citescorepercentile",
                    "subjectarea",
                    "subjectcode",
                    "category",
                }
            )

            if not has_rank_context:
                continue

            percentile = first_value_by_keys(
                child,
                {
                    "percentile",
                    "citescorepercentile",
                },
            )

            rank = first_value_by_keys(
                child,
                {
                    "rank",
                    "citescorerank",
                },
            )

            rank_out_of = first_value_by_keys(
                child,
                {
                    "rankoutof",
                    "outof",
                    "citescorerankoutof",
                },
            )

            category = first_value_by_keys(
                child,
                {
                    "category",
                    "subject",
                    "subjectarea",
                    "subjectname",
                    "description",
                },
            )

            subject_code = first_value_by_keys(
                child,
                {
                    "subjectcode",
                    "code",
                },
            )

            if percentile or rank or category or subject_code:
                rank_records.append(
                    {
                        "percentile": percentile,
                        "rank": rank,
                        "rank_out_of": rank_out_of,
                        "category": category,
                        "subject_code": subject_code,
                    }
                )

        return rank_records

    def best_rank_record(
        rank_records: list[dict[str, str]],
    ) -> dict[str, str]:
        if not rank_records:
            return {
                "percentile": "",
                "rank": "",
                "rank_out_of": "",
                "category": "",
                "subject_code": "",
            }

        def sort_key(record: dict[str, str]) -> float:
            try:
                return float(record.get("percentile") or -1)
            except ValueError:
                return -1

        return sorted(
            rank_records,
            key=sort_key,
            reverse=True,
        )[0]

    records: list[dict[str, str]] = []

    for node in iter_nested_values(payload):
        if not isinstance(node, dict):
            continue

        node_keys = {
            compact_key(key)
            for key in node.keys()
        }

        has_citescore_context = any(
            "citescore" in key
            for key in node_keys
        )

        if not has_citescore_context:
            continue

        year = first_value_by_keys(
            node,
            {
                "year",
                "citescoreyear",
                "citescorecurrentmetricyear",
                "citescoretrackeryear",
            },
        )

        citescore = first_value_by_keys(
            node,
            {
                "citescorecurrentmetric",
                "citescoremetric",
                "citescorevalue",
                "citescore",
                "currentmetric",
            },
        )

        # Do not store the year as the CiteScore value.
        if not citescore or looks_like_year(citescore):
            continue

        # CiteScore should be numeric. This avoids storing labels/status text.
        if not looks_numeric(citescore):
            continue

        rank_record = best_rank_record(
            collect_rank_records(node)
        )

        percentile = rank_record["percentile"]
        quartile = percentile_to_quartile(percentile)

        records.append(
            {
                "year": year,
                "citescore": citescore,
                "percentile": percentile,
                "rank": rank_record["rank"],
                "rank_out_of": rank_record["rank_out_of"],
                "category": rank_record["category"],
                "subject_code": rank_record["subject_code"],
                "quartile": quartile,
            }
        )

    seen: set[tuple[str, str, str, str]] = set()
    unique_records: list[dict[str, str]] = []

    for record in records:
        identity = (
            record["year"],
            record["citescore"],
            record["percentile"],
            record["category"],
        )

        if identity in seen:
            continue

        seen.add(identity)
        unique_records.append(record)

    return unique_records

def latest_citescore(
    records: list[dict[str, str]],
) -> dict[str, str]:
    if not records:
        return {
            "year": "",
            "citescore": "",
            "percentile": "",
            "rank": "",
            "rank_out_of": "",
            "category": "",
            "subject_code": "",
            "quartile": "",
        }

    def sort_key(record: dict[str, str]) -> tuple[int, float]:
        try:
            year = int(record.get("year") or -1)
        except ValueError:
            year = -1

        try:
            percentile = float(record.get("percentile") or -1)
        except ValueError:
            percentile = -1

        return year, percentile

    return sorted(
        records,
        key=sort_key,
        reverse=True,
    )[0]


def fetch_elsevier_serial_title(
    issn: str,
    api_key: str,
    insttoken: str | None,
    timeout: int,
) -> dict[str, Any]:
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
    }

    if insttoken:
        headers["X-ELS-Insttoken"] = insttoken

    response = requests.get(
        SERIAL_TITLE_API.format(
            issn=issn.replace("-", "")
        ),
        headers=headers,
        params={
            "view": "CITESCORE",
            "httpAccept": "application/json",
        },
        timeout=timeout,
    )

    if response.status_code == 404:
        return {
            "found": False,
            "status_code": response.status_code,
            "payload": {},
        }

    if response.status_code in {401, 403}:
        raise RuntimeError(
            "Elsevier API authentication failed. Check ELSEVIER_API_KEY "
            "and, if your institution requires it, ELSEVIER_INSTTOKEN."
        )

    response.raise_for_status()

    return {
        "found": True,
        "status_code": response.status_code,
        "payload": response.json(),
    }


def extract_links(payload: Any) -> dict[str, str]:
    links: dict[str, str] = {}

    for node in iter_nested_values(payload):
        if not isinstance(node, dict):
            continue

        if "link" not in node:
            continue

        raw_links = node["link"]

        if not isinstance(raw_links, list):
            raw_links = [raw_links]

        for link in raw_links:
            if not isinstance(link, dict):
                continue

            ref = text_value(
                link.get("@ref")
                or link.get("ref")
            )

            href = text_value(
                link.get("@href")
                or link.get("href")
            )

            if ref and href:
                links[ref] = href

    return links


def source_id_from_links_or_payload(
    links: dict[str, str],
    payload: Any,
) -> str:
    for href in links.values():
        match = re.search(
            r"sourceid/(\d+)",
            href,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

    value = find_first_key(
        payload,
        [
            "source-id",
            "sourceId",
            "source_id",
            "dc:identifier",
        ],
    )

    text = text_value(value)

    match = re.search(r"(\d+)", text)

    if match:
        return match.group(1)

    return ""


def parse_elsevier_payload(
    issn: str,
    payload: dict[str, Any],
    raw_payload: bool,
) -> dict[str, Any]:
    links = extract_links(payload)

    title = text_value(
        find_first_key(
            payload,
            [
                "dc:title",
                "title",
                "prism:publicationName",
            ],
        )
    )

    publisher = text_value(
        find_first_key(
            payload,
            [
                "dc:publisher",
                "publisher",
            ],
        )
    )

    prism_issn = normalize_issn(
        text_value(
            find_first_key(
                payload,
                [
                    "prism:issn",
                    "issn",
                ],
            )
        )
    )

    prism_eissn = normalize_issn(
        text_value(
            find_first_key(
                payload,
                [
                    "prism:eIssn",
                    "eIssn",
                    "eissn",
                ],
            )
        )
    )

    sjr = latest_metric(
        extract_year_value_list(
            payload,
            ["SJRList", "SJR-list"],
            ["SJR"],
        )
    )

    snip = latest_metric(
        extract_year_value_list(
            payload,
            ["SNIPList", "SNIP-list"],
            ["SNIP"],
        )
    )

    ipp = latest_metric(
        extract_year_value_list(
            payload,
            ["IPPList", "IPP-list"],
            ["IPP"],
        )
    )

    citescore_records = extract_citescore_records(payload)
    citescore = latest_citescore(citescore_records)

    source_id = source_id_from_links_or_payload(
        links,
        payload,
    )

    scopus_source_url = ""

    if source_id:
        scopus_source_url = f"https://www.scopus.com/sourceid/{source_id}"

    elif "scopus-source" in links:
        scopus_source_url = links["scopus-source"]

    record: dict[str, Any] = {
        "source": "Elsevier Serial Title API / Scopus",
        "queried_issn": issn,
        "title": title,
        "publisher": publisher,
        "issn": prism_issn,
        "eissn": prism_eissn,
        "source_id": source_id,
        "scopus_source_url": scopus_source_url,
        "sjr": sjr["value"],
        "sjr_year": sjr["year"],
        "snip": snip["value"],
        "snip_year": snip["year"],
        "ipp": ipp["value"],
        "ipp_year": ipp["year"],
        "citescore": citescore["citescore"],
        "citescore_year": citescore["year"],
        "citescore_percentile": citescore["percentile"],
        "citescore_quartile": citescore["quartile"],
        "citescore_category": (
        citescore.get("category", "")
        or citescore.get("subject_area", "")
        ),
"citescore_subject_code": citescore.get("subject_code", ""),
),
"citescore_subject_code": citescore.get("subject_code", ""),
"citescore_rank": citescore.get("rank", ""),
"citescore_rank_out_of": citescore.get("rank_out_of", ""),
        "citescore_records": citescore_records,
        "updated_at": utc_timestamp(),
    }

    if raw_payload:
        record["raw_payload"] = payload

    return record


def load_existing_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def write_json(
    path: Path,
    data: Any,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(path)


def build_publication_metrics(
    publications: list[dict[str, Any]],
    source_metrics_by_issn: dict[str, dict[str, Any]],
    existing_publication_metrics: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}

    empty_elsevier_fields = {
        "source_metric_source": "",
        "source_title": "",
        "source_id": "",
        "scopus_source_url": "",
        "publisher": "",
        "sjr": "",
        "sjr_year": "",
        "snip": "",
        "snip_year": "",
        "ipp": "",
        "ipp_year": "",
        "citescore": "",
        "citescore_year": "",
        "citescore_percentile": "",
        "citescore_quartile": "",
        "citescore_subject_code": "",
        "citescore_category": "",
        "citescore_rank": "",
        "citescore_rank_out_of": "",
    }

    for publication in publications:
        key = publication["key"]

        existing = existing_publication_metrics.get(key, {})

        if not isinstance(existing, dict):
            existing = {}

        matched_issn = ""
        matched_source = None

        for issn in publication["all_issns"]:
            candidate = source_metrics_by_issn.get(issn)

            if not candidate:
                continue

            # Important:
            # A not-found ISSN is still stored in source_metrics_by_issn,
            # but it must not count as an Elsevier match.
            if not candidate.get("found"):
                continue

            matched_issn = issn
            matched_source = candidate
            break

        record: dict[str, Any] = {
            **existing,
            "title": publication["title"],
            "year": publication["year"],
            "type": publication["type"],
            "journal": publication["journal"],
            "booktitle": publication["booktitle"],
            "issn": publication["issn"],
            "print_issn": publication["print_issn"],
            "elsevier_matched": matched_source is not None,
            "elsevier_matched_issn": matched_issn,
        }

        if matched_source:
            record.update(
                {
                    "source_metric_source": matched_source.get("source", ""),
                    "source_title": matched_source.get("title", ""),
                    "source_id": matched_source.get("source_id", ""),
                    "scopus_source_url": matched_source.get("scopus_source_url", ""),
                    "publisher": matched_source.get("publisher", ""),
                    "sjr": matched_source.get("sjr", ""),
                    "sjr_year": matched_source.get("sjr_year", ""),
                    "snip": matched_source.get("snip", ""),
                    "snip_year": matched_source.get("snip_year", ""),
                    "ipp": matched_source.get("ipp", ""),
                    "ipp_year": matched_source.get("ipp_year", ""),
                    "citescore": matched_source.get("citescore", ""),
                    "citescore_year": matched_source.get("citescore_year", ""),
                    "citescore_percentile": matched_source.get("citescore_percentile", ""),
"citescore_quartile": matched_source.get("citescore_quartile", ""),
"citescore_category": matched_source.get("citescore_category", ""),
"citescore_subject_code": matched_source.get("citescore_subject_code", ""),
"citescore_rank": matched_source.get("citescore_rank", ""),
"citescore_rank_out_of": matched_source.get("citescore_rank_out_of", ""),
                }
            )
        else:
            record.update(empty_elsevier_fields)

        output[key] = record

    return output

def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--bibliography",
        type=Path,
        default=Path("_bibliography/publications.bib"),
    )

    parser.add_argument(
        "--source-output",
        type=Path,
        default=Path("_data/elsevier_source_metrics.json"),
    )

    parser.add_argument(
        "--publication-output",
        type=Path,
        default=Path("_data/publication_metrics.json"),
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.25,
        help="Delay between Elsevier API calls, in seconds",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
    )

    parser.add_argument(
        "--include-raw-payload",
        action="store_true",
        help="Store raw Elsevier JSON payloads for debugging",
    )

    args = parser.parse_args()

    api_key = os.getenv("ELSEVIER_API_KEY", "").strip()
    insttoken = os.getenv("ELSEVIER_INSTTOKEN", "").strip() or None

    if not api_key:
        print(
            "ERROR: ELSEVIER_API_KEY is not configured.",
            file=sys.stderr,
        )
        return 1

    try:
        publications = load_bibtex_publications(
            args.bibliography
        )

        unique_issns = sorted(
            {
                issn
                for publication in publications
                for issn in publication["all_issns"]
                if issn
            }
        )

        source_metrics_by_issn: dict[str, dict[str, Any]] = {}

        print(f"Unique ISSNs to query: {len(unique_issns)}")

        for index, issn in enumerate(unique_issns, start=1):
            print(f"[{index}/{len(unique_issns)}] Querying {issn}")

            result = fetch_elsevier_serial_title(
                issn=issn,
                api_key=api_key,
                insttoken=insttoken,
                timeout=args.timeout,
            )

            if not result["found"]:
                source_metrics_by_issn[issn] = {
                    "source": "Elsevier Serial Title API / Scopus",
                    "queried_issn": issn,
                    "found": False,
                    "updated_at": utc_timestamp(),
                }
                continue

            source_metrics_by_issn[issn] = {
                "found": True,
                **parse_elsevier_payload(
                    issn=issn,
                    payload=result["payload"],
                    raw_payload=args.include_raw_payload,
                ),
            }

            if args.delay:
                time.sleep(args.delay)

        existing_publication_metrics = load_existing_json(
            args.publication_output
        )

        publication_metrics = build_publication_metrics(
            publications=publications,
            source_metrics_by_issn=source_metrics_by_issn,
            existing_publication_metrics=existing_publication_metrics,
        )

        write_json(
            args.source_output,
            source_metrics_by_issn,
        )

        write_json(
            args.publication_output,
            publication_metrics,
        )

    except Exception as error:
        print(
            f"ERROR: {error}",
            file=sys.stderr,
        )
        return 1

    matched_publications = [
        key
        for key, metric in publication_metrics.items()
        if metric.get("elsevier_matched")
    ]

    unmatched_publications = [
        key
        for key, metric in publication_metrics.items()
        if not metric.get("elsevier_matched")
    ]

    print(f"Publications read: {len(publications)}")
    print(f"ISSNs queried: {len(unique_issns)}")
    print(f"Matched publications: {len(matched_publications)}")
    print(f"Unmatched publications: {len(unmatched_publications)}")
    print(f"Updated: {args.source_output}")
    print(f"Updated: {args.publication_output}")

    if unmatched_publications:
        print("Unmatched BibTeX keys:")
        for key in unmatched_publications:
            print(f"- {key}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
