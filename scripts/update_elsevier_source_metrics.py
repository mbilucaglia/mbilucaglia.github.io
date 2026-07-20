#!/usr/bin/env python3
"""Update per-publication Scopus/Elsevier metrics from BibTeX ISSNs.

Inputs:
- _bibliography/publications.bib
- _data/asjc_codes.json
- _data/publication_metrics.json, if already present
- ELSEVIER_API_KEY environment variable
- Optional: ELSEVIER_INSTTOKEN environment variable

Outputs:
- _data/elsevier_source_metrics.json
- _data/publication_metrics.json

Selection rule:
1. Parse each BibTeX entry.
2. Extract issn and print_issn.
3. Query Elsevier Serial Title API by ISSN.
4. Extract the current CiteScore for that source.
5. Extract all available CiteScore subject-ranking records.
6. Select the record with the highest percentile.
7. Convert percentile to quartile.
8. Convert ASJC subject code to category using _data/asjc_codes.json.

The script preserves existing Google Scholar fields in publication_metrics.json.
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


GOOGLE_SCHOLAR_FIELDS = {
    "google_scholar_citation_id",
    "google_scholar_citations",
    "google_scholar_link",
    "google_scholar_match_score",
    "google_scholar_updated_at",
}


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    text = str(value)
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


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


def issn_for_api(issn: str) -> str:
    return issn.replace("-", "")


def parse_float(value: Any, default: float = -1.0) -> float:
    if value is None:
        return default

    text = str(value).strip()
    text = text.replace("%", "").replace(",", ".")

    match = re.search(r"-?\d+(\.\d+)?", text)

    if not match:
        return default

    try:
        return float(match.group(0))
    except ValueError:
        return default


def parse_int(value: Any, default: int = -1) -> int:
    number = parse_float(value, default=float(default))

    try:
        return int(number)
    except ValueError:
        return default


def looks_like_year(value: Any) -> bool:
    return bool(re.fullmatch(r"20\d{2}", str(value or "").strip()))


def looks_numeric(value: Any) -> bool:
    return parse_float(value, default=-999999) != -999999


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

        issns: list[str] = []

        for candidate in [issn, print_issn]:
            if candidate and candidate not in issns:
                issns.append(candidate)

        pages = normalize_text(
            extract_bibtex_field(entry, "pages")
        )

        pages_as_issn = normalize_issn(pages)

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
                "issns": issns,
                "pages": pages,
                "pages_as_issn_warning": pages_as_issn,
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


def first_value_by_keys(
    node: dict[str, Any],
    possible_keys: set[str],
) -> str:
    for key, value in node.items():
        if compact_key(key) in possible_keys:
            return text_value(value)

    return ""


def find_first_key(
    payload: Any,
    possible_keys: set[str],
) -> str:
    for node in iter_nested_values(payload):
        if not isinstance(node, dict):
            continue

        value = first_value_by_keys(
            node,
            possible_keys,
        )

        if value:
            return value

    return ""


def load_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(data, dict):
        return {}

    return data


def load_asjc_codes(path: Path) -> dict[str, str]:
    data = load_json_dict(path)

    return {
        str(code).strip(): str(name).strip()
        for code, name in data.items()
        if str(code).strip() and str(name).strip()
    }


def asjc_name(
    subject_code: str | None,
    asjc_codes: dict[str, str],
) -> str:
    code = str(subject_code or "").strip()

    if not code:
        return ""

    return asjc_codes.get(code, "")


def clean_category(value: str | None) -> str:
    text = str(value or "").strip()

    if not text:
        return ""

    if re.fullmatch(r"\d+", text):
        return ""

    if re.fullmatch(r"Q[1-4]", text.upper()):
        return ""

    return text


def percentile_to_quartile(value: str | None) -> str:
    percentile = parse_float(value, default=-1)

    if percentile < 0:
        return ""

    if 0 <= percentile <= 1:
        percentile *= 100

    if percentile < 25:
        return "Q4"

    if percentile < 50:
        return "Q3"

    if percentile < 75:
        return "Q2"

    if percentile <= 100:
        return "Q1"

    return ""


def extract_links(payload: Any) -> dict[str, str]:
    links: dict[str, str] = {}

    for node in iter_nested_values(payload):
        if not isinstance(node, dict):
            continue

        raw_links = None

        for key, value in node.items():
            if compact_key(key) == "link":
                raw_links = value
                break

        if raw_links is None:
            continue

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


def source_id_from_payload(
    payload: Any,
    links: dict[str, str],
) -> str:
    for href in links.values():
        match = re.search(
            r"sourceid/(\d+)",
            href,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

    identifier = find_first_key(
        payload,
        {
            "sourceid",
            "sourceid",
            "sourceid",
            "dcidentifier",
        },
    )

    match = re.search(r"\d+", identifier)

    if match:
        return match.group(0)

    return ""


def extract_current_citescore(payload: Any) -> tuple[str, str]:
    """Return current CiteScore value and year.

    This deliberately prioritizes explicit current-metric keys.
    It does not infer CiteScore from percentile/rank rows.
    """

    current_metric_keys = {
        "citescorecurrentmetric",
        "citescoremetric",
        "currentmetric",
    }

    current_year_keys = {
        "citescorecurrentmetricyear",
        "citescoreyear",
        "currentmetricyear",
        "year",
    }

    candidates: list[tuple[str, str, int]] = []

    for node in iter_nested_values(payload):
        if not isinstance(node, dict):
            continue

        node_keys = {
            compact_key(key): key
            for key in node.keys()
        }

        score = ""

        for compact, original in node_keys.items():
            if compact in current_metric_keys:
                value = text_value(node[original])

                if looks_numeric(value) and not looks_like_year(value):
                    score = value.replace(",", ".")
                    break

        if not score:
            continue

        year = ""

        for compact, original in node_keys.items():
            if compact in current_year_keys:
                candidate_year = text_value(node[original])

                if looks_like_year(candidate_year):
                    year = candidate_year
                    break

        priority = 2 if "citescorecurrentmetric" in node_keys else 1

        candidates.append(
            (
                score,
                year,
                priority,
            )
        )

    if not candidates:
        return "", ""

    def sort_key(item: tuple[str, str, int]) -> tuple[int, int]:
        score, year, priority = item

        return (
            priority,
            parse_int(year, default=-1),
        )

    score, year, _priority = sorted(
        candidates,
        key=sort_key,
        reverse=True,
    )[0]

    return score, year


def extract_metric_year_value_list(
    payload: Any,
    list_keys: set[str],
    item_keys: set[str],
) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []

    for node in iter_nested_values(payload):
        if not isinstance(node, dict):
            continue

        for key, value in node.items():
            if compact_key(key) not in list_keys:
                continue

            for child in iter_nested_values(value):
                if not isinstance(child, dict):
                    continue

                for child_key, child_value in child.items():
                    if compact_key(child_key) not in item_keys:
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
                        else:
                            year = ""
                            metric_value = text_value(item)

                        if metric_value:
                            records.append(
                                {
                                    "year": year,
                                    "value": metric_value,
                                }
                            )

    return records


def latest_metric(records: list[dict[str, str]]) -> dict[str, str]:
    clean_records = [
        record
        for record in records
        if record.get("value")
    ]

    if not clean_records:
        return {
            "year": "",
            "value": "",
        }

    def sort_key(record: dict[str, str]) -> int:
        return parse_int(
            record.get("year"),
            default=-1,
        )

    return sorted(
        clean_records,
        key=sort_key,
        reverse=True,
    )[0]


def extract_ranking_records(payload: Any) -> list[dict[str, str]]:
    """Extract CiteScore ranking records.

    These are subject-ranking rows, not independent CiteScore values.
    The chosen row is the one with the highest percentile.
    """

    records: list[dict[str, str]] = []

    for node in iter_nested_values(payload):
        if not isinstance(node, dict):
            continue

        percentile = first_value_by_keys(
            node,
            {
                "percentile",
                "citescorepercentile",
                "percentilevalue",
            },
        )

        subject_code = first_value_by_keys(
            node,
            {
                "subjectcode",
                "asjccode",
                "code",
            },
        )

        category = clean_category(
            first_value_by_keys(
                node,
                {
                    "category",
                    "subject",
                    "subjectarea",
                    "subjectname",
                    "description",
                },
            )
        )

        rank = first_value_by_keys(
            node,
            {
                "rank",
                "citescorerank",
            },
        )

        rank_out_of = first_value_by_keys(
            node,
            {
                "rankoutof",
                "outof",
                "citescorerankoutof",
            },
        )

        if not percentile:
            continue

        if not subject_code and not category:
            continue

        records.append(
            {
                "percentile": percentile,
                "quartile": percentile_to_quartile(percentile),
                "rank": rank,
                "rank_out_of": rank_out_of,
                "category": category,
                "subject_code": subject_code,
            }
        )

    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str, str, str]] = set()

    for record in records:
        identity = (
            record.get("percentile", ""),
            record.get("quartile", ""),
            record.get("rank", ""),
            record.get("rank_out_of", ""),
            record.get("category", ""),
            record.get("subject_code", ""),
        )

        if identity in seen:
            continue

        seen.add(identity)
        deduped.append(record)

    return deduped


def select_highest_percentile_record(
    records: list[dict[str, str]],
) -> dict[str, str]:
    if not records:
        return {
            "percentile": "",
            "quartile": "",
            "rank": "",
            "rank_out_of": "",
            "category": "",
            "subject_code": "",
        }

    def sort_key(record: dict[str, str]) -> tuple[float, int]:
        percentile = parse_float(
            record.get("percentile"),
            default=-1,
        )

        rank = parse_int(
            record.get("rank"),
            default=999999,
        )

        # Highest percentile first.
        # If tied, lower rank number first.
        return (
            percentile,
            -rank,
        )

    selected = sorted(
        records,
        key=sort_key,
        reverse=True,
    )[0]

    return {
        **selected,
        "quartile": percentile_to_quartile(
            selected.get("percentile")
        ),
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
            issn=issn_for_api(issn)
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
            "and, if required, ELSEVIER_INSTTOKEN."
        )

    response.raise_for_status()

    return {
        "found": True,
        "status_code": response.status_code,
        "payload": response.json(),
    }


def parse_elsevier_payload(
    issn: str,
    payload: dict[str, Any],
    status_code: int,
    asjc_codes: dict[str, str],
    include_raw_payload: bool,
) -> dict[str, Any]:
    links = extract_links(payload)
    source_id = source_id_from_payload(
        payload,
        links,
    )

    scopus_source_url = ""

    if source_id:
        scopus_source_url = f"https://www.scopus.com/sourceid/{source_id}"
    elif links.get("scopus-source"):
        scopus_source_url = links["scopus-source"]

    source_title = find_first_key(
        payload,
        {
            "dctitle",
            "title",
            "prismpublicationname",
        },
    )

    publisher = find_first_key(
        payload,
        {
            "dcpublisher",
            "publisher",
        },
    )

    source_issn = normalize_issn(
        find_first_key(
            payload,
            {
                "prismissn",
                "issn",
            },
        )
    )

    source_eissn = normalize_issn(
        find_first_key(
            payload,
            {
                "prismeissn",
                "eissn",
            },
        )
    )

    citescore, citescore_year = extract_current_citescore(payload)

    ranking_records = extract_ranking_records(payload)

    selected_rank = select_highest_percentile_record(
        ranking_records
    )

    subject_code = selected_rank.get("subject_code", "")

    category = (
        clean_category(selected_rank.get("category"))
        or asjc_name(subject_code, asjc_codes)
    )

    sjr = latest_metric(
        extract_metric_year_value_list(
            payload,
            {"sjrlist", "sjrlist"},
            {"sjr"},
        )
    )

    snip = latest_metric(
        extract_metric_year_value_list(
            payload,
            {"sniplist", "sniplist"},
            {"snip"},
        )
    )

    record: dict[str, Any] = {
        "found": True,
        "status_code": status_code,
        "source": "Elsevier Serial Title API / Scopus",
        "queried_issn": issn,
        "title": source_title,
        "publisher": publisher,
        "issn": source_issn,
        "eissn": source_eissn,
        "source_id": source_id,
        "scopus_source_url": scopus_source_url,
        "citescore": citescore,
        "citescore_year": citescore_year,
        "citescore_percentile": selected_rank.get("percentile", ""),
        "citescore_quartile": selected_rank.get("quartile", ""),
        "citescore_rank": selected_rank.get("rank", ""),
        "citescore_rank_out_of": selected_rank.get("rank_out_of", ""),
        "citescore_subject_code": subject_code,
        "citescore_category": category,
        "citescore_ranking_selection": "highest_percentile",
        "citescore_ranking_records": [
            {
                **ranking,
                "category": (
                    clean_category(ranking.get("category"))
                    or asjc_name(ranking.get("subject_code"), asjc_codes)
                ),
                "quartile": percentile_to_quartile(
                    ranking.get("percentile")
                ),
            }
            for ranking in ranking_records
        ],
        "sjr": sjr.get("value", ""),
        "sjr_year": sjr.get("year", ""),
        "snip": snip.get("value", ""),
        "snip_year": snip.get("year", ""),
        "updated_at": utc_timestamp(),
    }

    if include_raw_payload:
        record["raw_payload"] = payload

    return record


def empty_scopus_fields() -> dict[str, Any]:
    return {
        "source_metric_source": "",
        "source_title": "",
        "source_id": "",
        "scopus_source_url": "",
        "publisher": "",
        "elsevier_matched": False,
        "elsevier_matched_issn": "",
        "citescore": "",
        "citescore_year": "",
        "citescore_percentile": "",
        "citescore_quartile": "",
        "citescore_rank": "",
        "citescore_rank_out_of": "",
        "citescore_subject_code": "",
        "citescore_category": "",
        "citescore_ranking_selection": "",
        "sjr": "",
        "sjr_year": "",
        "snip": "",
        "snip_year": "",
    }


def preserve_google_scholar_fields(
    existing: dict[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in existing.items()
        if key in GOOGLE_SCHOLAR_FIELDS
    }


def build_publication_metrics(
    publications: list[dict[str, Any]],
    source_metrics_by_issn: dict[str, dict[str, Any]],
    existing_publication_metrics: dict[str, Any],
) -> dict[str, Any]:
    output: dict[str, Any] = {}

    for publication in publications:
        key = publication["key"]

        existing = existing_publication_metrics.get(key, {})

        if not isinstance(existing, dict):
            existing = {}

        record: dict[str, Any] = {
            **preserve_google_scholar_fields(existing),
            "title": publication["title"],
            "year": publication["year"],
            "type": publication["type"],
            "journal": publication["journal"],
            "booktitle": publication["booktitle"],
            "issn": publication["issn"],
            "print_issn": publication["print_issn"],
        }

        matched_issn = ""
        matched_source: dict[str, Any] | None = None

        for issn in publication["issns"]:
            candidate = source_metrics_by_issn.get(issn)

            if not candidate:
                continue

            if not candidate.get("found"):
                continue

            matched_issn = issn
            matched_source = candidate
            break

        if matched_source:
            record.update(
                {
                    "source_metric_source": matched_source.get("source", ""),
                    "source_title": matched_source.get("title", ""),
                    "source_id": matched_source.get("source_id", ""),
                    "scopus_source_url": matched_source.get("scopus_source_url", ""),
                    "publisher": matched_source.get("publisher", ""),
                    "elsevier_matched": True,
                    "elsevier_matched_issn": matched_issn,
                    "citescore": matched_source.get("citescore", ""),
                    "citescore_year": matched_source.get("citescore_year", ""),
                    "citescore_percentile": matched_source.get(
                        "citescore_percentile",
                        "",
                    ),
                    "citescore_quartile": matched_source.get(
                        "citescore_quartile",
                        "",
                    ),
                    "citescore_rank": matched_source.get("citescore_rank", ""),
                    "citescore_rank_out_of": matched_source.get(
                        "citescore_rank_out_of",
                        "",
                    ),
                    "citescore_subject_code": matched_source.get(
                        "citescore_subject_code",
                        "",
                    ),
                    "citescore_category": matched_source.get(
                        "citescore_category",
                        "",
                    ),
                    "citescore_ranking_selection": matched_source.get(
                        "citescore_ranking_selection",
                        "",
                    ),
                    "sjr": matched_source.get("sjr", ""),
                    "sjr_year": matched_source.get("sjr_year", ""),
                    "snip": matched_source.get("snip", ""),
                    "snip_year": matched_source.get("snip_year", ""),
                }
            )

        else:
            record.update(empty_scopus_fields())

        if publication.get("pages_as_issn_warning"):
            record["warning_pages_field_looks_like_issn"] = publication[
                "pages_as_issn_warning"
            ]

        output[key] = record

    return output


def write_json(path: Path, data: Any) -> None:
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Update Scopus/Elsevier source metrics by BibTeX ISSN. "
            "Writes per-source metrics and merges per-publication Scopus "
            "metrics into publication_metrics.json while preserving "
            "Google Scholar citation fields."
        )
    )

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
        asjc_codes = load_asjc_codes(args.asjc_codes)

        publications = load_bibtex_publications(args.bibliography)

        unique_issns = sorted(
            {
                issn
                for publication in publications
                for issn in publication["issns"]
                if issn
            }
        )

        source_metrics_by_issn: dict[str, dict[str, Any]] = {}

        print(f"Publications read: {len(publications)}")
        print(f"Unique ISSNs to query: {len(unique_issns)}")
        print(f"ASJC codes loaded: {len(asjc_codes)}")

        for index, issn in enumerate(unique_issns, start=1):
            print(f"[{index}/{len(unique_issns)}] Querying ISSN {issn}")

            result = fetch_elsevier_serial_title(
                issn=issn,
                api_key=api_key,
                insttoken=insttoken,
                timeout=args.timeout,
            )

            if not result["found"]:
                source_metrics_by_issn[issn] = {
                    "found": False,
                    "status_code": result["status_code"],
                    "source": "Elsevier Serial Title API / Scopus",
                    "queried_issn": issn,
                    "updated_at": utc_timestamp(),
                }

            else:
                source_metrics_by_issn[issn] = parse_elsevier_payload(
                    issn=issn,
                    payload=result["payload"],
                    status_code=result["status_code"],
                    asjc_codes=asjc_codes,
                    include_raw_payload=args.include_raw_payload,
                )

            if args.delay:
                time.sleep(args.delay)

        existing_publication_metrics = load_json_dict(
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

    matched_sources = [
        issn
        for issn, source in source_metrics_by_issn.items()
        if source.get("found")
    ]

    matched_publications = [
        key
        for key, metric in publication_metrics.items()
        if isinstance(metric, dict)
        and metric.get("elsevier_matched")
    ]

    scholar_publications = [
        key
        for key, metric in publication_metrics.items()
        if isinstance(metric, dict)
        and "google_scholar_citations" in metric
    ]

    publications_with_citescore = [
        key
        for key, metric in publication_metrics.items()
        if isinstance(metric, dict)
        and metric.get("citescore")
    ]

    publications_with_category = [
        key
        for key, metric in publication_metrics.items()
        if isinstance(metric, dict)
        and metric.get("citescore_category")
    ]

    warnings = [
        key
        for key, metric in publication_metrics.items()
        if isinstance(metric, dict)
        and metric.get("warning_pages_field_looks_like_issn")
    ]

    print(f"ISSNs matched to Scopus/Elsevier: {len(matched_sources)}")
    print(f"Publications matched to Scopus/Elsevier: {len(matched_publications)}")
    print(f"Publications with Google Scholar citations preserved: {len(scholar_publications)}")
    print(f"Publications with CiteScore: {len(publications_with_citescore)}")
    print(f"Publications with CiteScore category: {len(publications_with_category)}")
    print(f"Updated: {args.source_output}")
    print(f"Updated: {args.publication_output}")

    if warnings:
        print(
            "WARNING: These BibTeX entries have a pages field that looks like an ISSN:"
        )
        for key in warnings:
            value = publication_metrics[key]["warning_pages_field_looks_like_issn"]
            print(f"- {key}: pages looks like ISSN {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
