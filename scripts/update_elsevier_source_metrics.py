#!/usr/bin/env python3
"""Fetch Elsevier/Scopus source metrics by ISSN.

Inputs:
- _bibliography/publications.bib
- _data/asjc_codes.json
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


def compact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def normalize_issn(value: str | None) -> str:
    if not value:
        return ""

    text = str(value).strip()
    text = text.replace("{", "").replace("}", "")
    text = text.replace("ISSN", "").replace("issn", "")

    characters = [
        character.upper()
        for character in text
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

    text = str(value)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


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

        all_issns: list[str] = []

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


def text_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, dict):
        for key in [
            "$",
            "#text",
            "_",
            "value",
            "@value",
            "text",
        ]:
            if key in value:
                return text_value(value[key])

    return ""


def first_value_by_compact_keys(
    node: dict[str, Any],
    possible_keys: set[str],
) -> str:
    for key, value in node.items():
        if compact_key(key) in possible_keys:
            return text_value(value)

    return ""


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


def extract_year_value_list(
    payload: Any,
    list_names: list[str],
    item_names: list[str],
) -> list[dict[str, str]]:
    """Extract metric values such as SJRList/SJR[@year]."""

    list_names_compact = {
        compact_key(name)
        for name in list_names
    }

    item_names_compact = {
        compact_key(name)
        for name in item_names
    }

    results: list[dict[str, str]] = []

    for node in iter_nested_values(payload):
        if not isinstance(node, dict):
            continue

        for key, value in node.items():
            if compact_key(key) not in list_names_compact:
                continue

            for child in iter_nested_values(value):
                if not isinstance(child, dict):
                    continue

                for child_key, child_value in child.items():
                    if compact_key(child_key) not in item_names_compact:
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
                            metric_value = text_value(item)

                            if metric_value:
                                results.append(
                                    {
                                        "year": "",
                                        "value": metric_value,
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


def percentile_to_quartile(value: str | None) -> str:
    """Convert CiteScore percentile to CiteScore quartile.

    Convention:
    - Q1: percentile >= 75
    - Q2: percentile >= 50 and < 75
    - Q3: percentile >= 25 and < 50
    - Q4: percentile < 25
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

    # Defensive handling if an API ever returns 0–1 instead of 0–100.
    if 0 <= percentile <= 1:
        percentile *= 100

    if percentile < 0 or percentile > 100:
        return ""

    if percentile < 25:
        return "Q4"

    if percentile < 50:
        return "Q3"

    if percentile < 75:
        return "Q2"

    return "Q1"


def normalize_quartile(value: str | None) -> str:
    if value is None:
        return ""

    text = str(value).strip().upper()

    match = re.search(r"\bQ[1-4]\b", text)

    if match:
        return match.group(0)

    return ""


def quartile_score(value: str) -> int:
    if value == "Q1":
        return 4

    if value == "Q2":
        return 3

    if value == "Q3":
        return 2

    if value == "Q4":
        return 1

    return 0


def looks_like_year(value: str) -> bool:
    return bool(re.fullmatch(r"20\d{2}", value.strip()))


def looks_numeric(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"\d+(\.\d+)?",
            value.strip().replace(",", "."),
        )
    )


def clean_category(value: str | None) -> str:
    text = str(value or "").strip()

    if not text:
        return ""

    # Do not treat ASJC numeric subject codes as category names.
    if re.fullmatch(r"\d+", text):
        return ""

    # Avoid storing quartile strings as category names.
    if re.fullmatch(r"Q[1-4]", text.upper()):
        return ""

    return text


def load_existing_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(data, dict):
        return {}

    return data


def load_asjc_codes(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(data, dict):
        return {}

    return {
        str(code).strip(): str(name).strip()
        for code, name in data.items()
        if str(code).strip() and str(name).strip()
    }


def asjc_category_name(
    subject_code: str | None,
    asjc_codes: dict[str, str],
) -> str:
    code = str(subject_code or "").strip()

    if not code:
        return ""

    return asjc_codes.get(code, "")


def category_from_record(
    record: dict[str, Any],
    asjc_codes: dict[str, str],
) -> str:
    return (
        clean_category(record.get("category", ""))
        or asjc_category_name(record.get("subject_code", ""), asjc_codes)
    )


def collect_rank_records(node: Any) -> list[dict[str, str]]:
    """Collect nested CiteScore rank/percentile/category records."""

    records: list[dict[str, str]] = []

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
                "outof",
                "percentile",
                "quartile",
                "citescorerank",
                "citescorerankoutof",
                "citescorepercentile",
                "citescorequartile",
                "subjectarea",
                "subjectname",
                "subjectcode",
                "category",
            }
        )

        if not has_rank_context:
            continue

        percentile = first_value_by_compact_keys(
            child,
            {
                "percentile",
                "citescorepercentile",
            },
        )

        direct_quartile = first_value_by_compact_keys(
            child,
            {
                "quartile",
                "citescorequartile",
            },
        )

        rank = first_value_by_compact_keys(
            child,
            {
                "rank",
                "citescorerank",
            },
        )

        rank_out_of = first_value_by_compact_keys(
            child,
            {
                "rankoutof",
                "outof",
                "citescorerankoutof",
            },
        )

        category = clean_category(
            first_value_by_compact_keys(
                child,
                {
                    "category",
                    "subject",
                    "subjectarea",
                    "subjectname",
                    "description",
                },
            )
        )

        subject_code = first_value_by_compact_keys(
            child,
            {
                "subjectcode",
                "code",
            },
        )

        quartile = (
            normalize_quartile(direct_quartile)
            or percentile_to_quartile(percentile)
        )

        if percentile or quartile or rank or category or subject_code:
            records.append(
                {
                    "percentile": percentile,
                    "quartile": quartile,
                    "rank": rank,
                    "rank_out_of": rank_out_of,
                    "category": category,
                    "subject_code": subject_code,
                }
            )

    return records


def best_rank_record(
    rank_records: list[dict[str, str]],
) -> dict[str, str]:
    """Choose the highest percentile rank record.

    This is appropriate for journal/source-level data. For non-article
    publication entries, build_publication_metrics() applies a more
    conservative publication-level selection.
    """

    if not rank_records:
        return {
            "percentile": "",
            "quartile": "",
            "rank": "",
            "rank_out_of": "",
            "category": "",
            "subject_code": "",
        }

    def sort_key(record: dict[str, str]) -> tuple[float, int]:
        try:
            percentile = float(
                str(record.get("percentile") or "-1")
                .replace("%", "")
                .replace(",", ".")
            )
        except ValueError:
            percentile = -1

        return (
            percentile,
            quartile_score(record.get("quartile", "")),
        )

    return sorted(
        rank_records,
        key=sort_key,
        reverse=True,
    )[0]


def worst_rank_record(
    rank_records: list[dict[str, str]],
) -> dict[str, str]:
    """Choose the lowest available percentile rank record.

    This is used for non-article entries such as conference proceedings,
    where broad source-level categories can otherwise overstate the quartile.
    """

    clean_records = [
        record
        for record in rank_records
        if record.get("percentile") or record.get("quartile")
    ]

    if not clean_records:
        return {
            "percentile": "",
            "quartile": "",
            "rank": "",
            "rank_out_of": "",
            "category": "",
            "subject_code": "",
        }

    def sort_key(record: dict[str, str]) -> tuple[float, int]:
        try:
            percentile = float(
                str(record.get("percentile") or "999")
                .replace("%", "")
                .replace(",", ".")
            )
        except ValueError:
            percentile = 999

        return (
            percentile,
            quartile_score(record.get("quartile", "")),
        )

    return sorted(
        clean_records,
        key=sort_key,
    )[0]


def extract_citescore_records(payload: Any) -> list[dict[str, str]]:
    """Extract CiteScore records from Elsevier Serial Title JSON."""

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

        year = first_value_by_compact_keys(
            node,
            {
                "year",
                "citescoreyear",
                "citescorecurrentmetricyear",
                "citescoretrackeryear",
            },
        )

        citescore = first_value_by_compact_keys(
            node,
            {
                "citescorecurrentmetric",
                "citescoremetric",
                "citescorevalue",
                "citescore",
                "currentmetric",
            },
        )

        if not citescore:
            continue

        # Avoid storing the metric year as the CiteScore value.
        if looks_like_year(citescore):
            continue

        # CiteScore should be numeric.
        if not looks_numeric(citescore):
            continue

        rank_record = best_rank_record(
            collect_rank_records(node)
        )

        percentile = rank_record.get("percentile", "")
        quartile = (
            rank_record.get("quartile", "")
            or percentile_to_quartile(percentile)
        )

        records.append(
            {
                "year": year,
                "citescore": citescore.replace(",", "."),
                "percentile": percentile,
                "quartile": quartile,
                "rank": rank_record.get("rank", ""),
                "rank_out_of": rank_record.get("rank_out_of", ""),
                "category": clean_category(
                    rank_record.get("category", "")
                ),
                "subject_code": rank_record.get("subject_code", ""),
            }
        )

    seen: set[tuple[str, str, str, str, str, str]] = set()
    unique_records: list[dict[str, str]] = []

    for record in records:
        identity = (
            record["year"],
            record["citescore"],
            record["percentile"],
            record["quartile"],
            record["category"],
            record["subject_code"],
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
            "quartile": "",
            "rank": "",
            "rank_out_of": "",
            "category": "",
            "subject_code": "",
        }

    def sort_key(record: dict[str, str]) -> tuple[int, float, int]:
        try:
            year = int(record.get("year") or -1)
        except ValueError:
            year = -1

        try:
            percentile = float(
                str(record.get("percentile") or "-1")
                .replace("%", "")
                .replace(",", ".")
            )
        except ValueError:
            percentile = -1

        return (
            year,
            percentile,
            quartile_score(record.get("quartile", "")),
        )

    return sorted(
        records,
        key=sort_key,
        reverse=True,
    )[0]


def conservative_citescore_record(
    matched_source: dict[str, Any],
) -> dict[str, str]:
    """Choose a conservative CiteScore record for non-article entries.

    For broad conference series, the highest percentile can be misleading.
    This function chooses the lowest percentile among available CiteScore
    records for the matched source.
    """

    records = matched_source.get("citescore_records", [])

    if not isinstance(records, list):
        records = []

    rank_records: list[dict[str, str]] = []

    for record in records:
        if not isinstance(record, dict):
            continue

        percentile = str(record.get("percentile", "")).strip()
        quartile = str(record.get("quartile", "")).strip()

        if not percentile and not quartile:
            continue

        rank_records.append(
            {
                "percentile": percentile,
                "quartile": (
                    normalize_quartile(quartile)
                    or percentile_to_quartile(percentile)
                ),
                "rank": str(record.get("rank", "")).strip(),
                "rank_out_of": str(record.get("rank_out_of", "")).strip(),
                "category": clean_category(record.get("category", "")),
                "subject_code": str(record.get("subject_code", "")).strip(),
            }
        )

    conservative_rank = worst_rank_record(rank_records)

    return {
        "citescore": str(matched_source.get("citescore", "")).strip(),
        "year": str(matched_source.get("citescore_year", "")).strip(),
        "percentile": conservative_rank.get("percentile", ""),
        "quartile": conservative_rank.get("quartile", ""),
        "category": conservative_rank.get("category", ""),
        "subject_code": conservative_rank.get("subject_code", ""),
        "rank": conservative_rank.get("rank", ""),
        "rank_out_of": conservative_rank.get("rank_out_of", ""),
    }


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
    asjc_codes: dict[str, str],
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
        "citescore": citescore.get("citescore", ""),
        "citescore_year": citescore.get("year", ""),
        "citescore_percentile": citescore.get("percentile", ""),
        "citescore_quartile": citescore.get("quartile", ""),
        "citescore_category": category_from_record(
            citescore,
            asjc_codes,
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


def empty_elsevier_fields() -> dict[str, str]:
    return {
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
        "citescore_category": "",
        "citescore_subject_code": "",
        "citescore_rank": "",
        "citescore_rank_out_of": "",
    }


def build_publication_metrics(
    publications: list[dict[str, Any]],
    source_metrics_by_issn: dict[str, dict[str, Any]],
    existing_publication_metrics: dict[str, Any],
    asjc_codes: dict[str, str],
) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}

    for publication in publications:
        key = publication["key"]

        existing = existing_publication_metrics.get(key, {})

        if not isinstance(existing, dict):
            existing = {}

        matched_issn = ""
        matched_source: dict[str, Any] | None = None

        for issn in publication["all_issns"]:
            candidate = source_metrics_by_issn.get(issn)

            if not candidate:
                continue

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
            if publication["type"] == "article":
                citescore_for_publication = {
                    "citescore": matched_source.get("citescore", ""),
                    "year": matched_source.get("citescore_year", ""),
                    "percentile": matched_source.get("citescore_percentile", ""),
                    "quartile": matched_source.get("citescore_quartile", ""),
                    "category": matched_source.get("citescore_category", ""),
                    "subject_code": matched_source.get("citescore_subject_code", ""),
                    "rank": matched_source.get("citescore_rank", ""),
                    "rank_out_of": matched_source.get("citescore_rank_out_of", ""),
                }
            else:
                citescore_for_publication = conservative_citescore_record(
                    matched_source
                )

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
                    "citescore": citescore_for_publication.get("citescore", ""),
                    "citescore_year": citescore_for_publication.get("year", ""),
                    "citescore_percentile": citescore_for_publication.get("percentile", ""),
                    "citescore_quartile": citescore_for_publication.get("quartile", ""),
                    "citescore_category": category_from_record(
                        citescore_for_publication,
                        asjc_codes,
                    ),
                    "citescore_subject_code": citescore_for_publication.get("subject_code", ""),
                    "citescore_rank": citescore_for_publication.get("rank", ""),
                    "citescore_rank_out_of": citescore_for_publication.get("rank_out_of", ""),
                }
            )
        else:
            record.update(empty_elsevier_fields())

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
        "--asjc-codes",
        type=Path,
        default=Path("_data/asjc_codes.json"),
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
        asjc_codes = load_asjc_codes(
            args.asjc_codes
        )

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

        print(f"ASJC codes loaded: {len(asjc_codes)}")
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
                    "found": False,
                    "source": "Elsevier Serial Title API / Scopus",
                    "queried_issn": issn,
                    "status_code": result["status_code"],
                    "updated_at": utc_timestamp(),
                }

                if args.delay:
                    time.sleep(args.delay)

                continue

            source_metrics_by_issn[issn] = {
                "found": True,
                "status_code": result["status_code"],
                **parse_elsevier_payload(
                    issn=issn,
                    payload=result["payload"],
                    raw_payload=args.include_raw_payload,
                    asjc_codes=asjc_codes,
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
            asjc_codes=asjc_codes,
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

    matched_with_citescore = [
        key
        for key, metric in publication_metrics.items()
        if metric.get("citescore")
    ]

    matched_with_quartile = [
        key
        for key, metric in publication_metrics.items()
        if metric.get("citescore_quartile")
    ]

    matched_with_category = [
        key
        for key, metric in publication_metrics.items()
        if metric.get("citescore_category")
    ]

    print(f"Publications read: {len(publications)}")
    print(f"ISSNs queried: {len(unique_issns)}")
    print(f"Matched publications: {len(matched_publications)}")
    print(f"Unmatched publications: {len(unmatched_publications)}")
    print(f"Publications with CiteScore: {len(matched_with_citescore)}")
    print(f"Publications with CiteScore quartile: {len(matched_with_quartile)}")
    print(f"Publications with CiteScore category: {len(matched_with_category)}")
    print(f"Updated: {args.source_output}")
    print(f"Updated: {args.publication_output}")

    if unmatched_publications:
        print("Unmatched BibTeX keys:")
        for key in unmatched_publications:
            print(f"- {key}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
