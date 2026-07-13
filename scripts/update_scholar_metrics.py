#!/usr/bin/env python3
"""Fetch Google Scholar metrics and most-cited papers via SerpAPI.

The script writes two outputs:

1. _data/scholar.json
   Jekyll data file containing citation indices and most-cited paper metadata.

2. _bibliography/top_cited.bib
   Generated BibTeX file containing matched entries from
   _bibliography/publications.bib, ordered by Google Scholar citation count.

The generated BibTeX file lets Jekyll-Scholar render the most-cited papers
with the same template used by the Publications page.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests


def utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )


def profile_url(scholar_id: str) -> str:
    return (
        "https://scholar.google.com/citations"
        f"?user={scholar_id}&hl=en"
    )


def parse_int(value: Any) -> int | None:
    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    text = str(value)
    digits = "".join(
        character
        for character in text
        if character.isdigit()
    )

    if not digits:
        return None

    return int(digits)


def extract_metric_value(
    table: list[dict[str, Any]],
    possible_keys: list[str],
) -> tuple[int | None, int | None, str | None]:
    for row in table:
        if not isinstance(row, dict):
            continue

        for key in possible_keys:
            values = row.get(key)

            if not isinstance(values, dict):
                continue

            total = parse_int(values.get("all"))

            recent_value = None
            recent_period = None

            for value_key, value in values.items():
                if value_key == "all":
                    continue

                if value_key.startswith("since_"):
                    recent_value = parse_int(value)
                    recent_period = (
                        "Since "
                        + value_key.removeprefix("since_")
                    )
                    break

            return (
                total,
                recent_value,
                recent_period,
            )

    return None, None, None


def normalize_article(
    article: dict[str, Any],
) -> dict[str, Any] | None:
    title = article.get("title")

    if not title:
        return None

    cited_by = article.get("cited_by", {})

    citations = 0

    if isinstance(cited_by, dict):
        citations = parse_int(cited_by.get("value")) or 0

    return {
        "title": title,
        "authors": article.get("authors"),
        "publication": article.get("publication"),
        "year": article.get("year"),
        "citations": citations,
        "link": article.get("link"),
        "citation_id": article.get("citation_id"),
    }


def fetch_serpapi_author(
    scholar_id: str,
    api_key: str,
    top_papers: int,
) -> dict[str, Any]:
    response = requests.get(
        "https://serpapi.com/search.json",
        params={
            "engine": "google_scholar_author",
            "author_id": scholar_id,
            "hl": "en",
            "api_key": api_key,
            # SerpAPI returns author articles sorted by citations by default.
            # Request at least 20 so title matching has enough candidates.
            # The endpoint supports up to 100 in one call.
            "num": min(max(top_papers, 20), 100),
        },
        timeout=60,
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("error"):
        raise RuntimeError(
            f"SerpAPI returned an error: {payload['error']}"
        )

    status = payload.get("search_metadata", {}).get("status")

    if status == "Error":
        raise RuntimeError(
            "SerpAPI search_metadata.status is Error"
        )

    cited_by = payload.get("cited_by", {})
    table = cited_by.get("table", [])

    if not isinstance(table, list):
        raise RuntimeError(
            "SerpAPI response does not contain cited_by.table"
        )

    citations, citations_recent, recent_period = extract_metric_value(
        table,
        ["citations"],
    )

    h_index, h_index_recent, h_recent_period = extract_metric_value(
        table,
        ["h_index", "indice_h"],
    )

    i10_index, i10_index_recent, i10_recent_period = extract_metric_value(
        table,
        ["i10_index", "indice_i10"],
    )

    missing = []

    if citations is None:
        missing.append("citations")

    if h_index is None:
        missing.append("h_index")

    if i10_index is None:
        missing.append("i10_index")

    if missing:
        raise RuntimeError(
            "SerpAPI response is missing: "
            + ", ".join(missing)
        )

    articles = payload.get("articles", [])

    if not isinstance(articles, list):
        articles = []

    normalized_articles = [
        article
        for article in (
            normalize_article(item)
            for item in articles
            if isinstance(item, dict)
        )
        if article is not None
    ]

    normalized_articles.sort(
        key=lambda item: item.get("citations", 0),
        reverse=True,
    )

    author = payload.get("author", {})

    if not isinstance(author, dict):
        author = {}

    return {
        "scholar_id": scholar_id,
        "profile_url": profile_url(scholar_id),
        "name": author.get("name"),
        "source": "Google Scholar via SerpAPI",
        "updated_at": utc_timestamp(),
        "recent_period": (
            recent_period
            or h_recent_period
            or i10_recent_period
        ),
        "citations": citations,
        "citations_recent": citations_recent,
        "h_index": h_index,
        "h_index_recent": h_index_recent,
        "i10_index": i10_index,
        "i10_index_recent": i10_index_recent,
        "top_cited_papers": normalized_articles[:top_papers],
    }


def normalize_title(value: str | None) -> str:
    if not value:
        return ""

    # Remove common BibTeX/LaTeX wrappers.
    value = value.replace("{", "").replace("}", "")
    value = value.replace("\\&", "&")
    value = value.replace("-", "-")
    value = value.replace("–", "-")
    value = value.replace("—", "-")

    # Convert a few common LaTeX accent patterns before stripping commands.
    value = re.sub(r'\\"([A-Za-z])', r"\1", value)
    value = re.sub(r"\\'([A-Za-z])", r"\1", value)
    value = re.sub(r"\\`([A-Za-z])", r"\1", value)
    value = re.sub(r"\\~([A-Za-z])", r"\1", value)
    value = re.sub(r"\\\^([A-Za-z])", r"\1", value)
    value = re.sub(r"\\o", "o", value)
    value = re.sub(r"\\O", "O", value)

    # Remove remaining LaTeX commands.
    value = re.sub(r"\\[a-zA-Z]+", " ", value)

    # Remove accents.
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character
        for character in value
        if not unicodedata.combining(character)
    )

    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)

    return " ".join(value.split())


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
                    entries.append(
                        text[start : position + 1]
                    )
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


def load_bibtex_entries(
    bibliography_path: Path,
) -> list[dict[str, str]]:
    if not bibliography_path.exists():
        raise FileNotFoundError(
            f"Bibliography file not found: {bibliography_path}"
        )

    text = bibliography_path.read_text(
        encoding="utf-8"
    )

    parsed_entries: list[dict[str, str]] = []

    for entry_text in split_bibtex_entries(text):
        key = bibtex_key(entry_text)
        title = extract_bibtex_field(
            entry_text,
            "title",
        )

        if not key or not title:
            continue

        parsed_entries.append(
            {
                "key": key,
                "title": title,
                "normalized_title": normalize_title(title),
                "entry": entry_text.strip(),
            }
        )

    return parsed_entries


def find_matching_bibtex_entry(
    paper_title: str,
    bibtex_entries: list[dict[str, str]],
) -> tuple[dict[str, str] | None, float]:
    normalized_paper_title = normalize_title(paper_title)

    if not normalized_paper_title:
        return None, 0.0

    for entry in bibtex_entries:
        if entry["normalized_title"] == normalized_paper_title:
            return entry, 1.0

    best_entry = None
    best_score = 0.0

    for entry in bibtex_entries:
        score = SequenceMatcher(
            None,
            normalized_paper_title,
            entry["normalized_title"],
        ).ratio()

        if score > best_score:
            best_entry = entry
            best_score = score

    if best_score >= 0.88 and best_entry is not None:
        return best_entry, best_score

    return None, best_score


def remove_existing_note_field(entry: str) -> str:
    lines = entry.splitlines()
    filtered_lines: list[str] = []

    skipping_note = False
    brace_depth = 0

    for line in lines:
        if not skipping_note and re.match(
            r"^\s*note\s*=",
            line,
            flags=re.IGNORECASE,
        ):
            skipping_note = True
            brace_depth = line.count("{") - line.count("}")

            if brace_depth <= 0:
                skipping_note = False

            continue

        if skipping_note:
            brace_depth += line.count("{") - line.count("}")

            if brace_depth <= 0:
                skipping_note = False

            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines).rstrip()


def add_citation_note_to_bibtex(
    entry: str,
    citations: int,
) -> str:
    cleaned_entry = remove_existing_note_field(entry)

    closing_position = cleaned_entry.rfind("}")

    if closing_position == -1:
        return entry

    body = cleaned_entry[:closing_position].rstrip()

    if not body.endswith(","):
        body += ","

    return (
        f"{body}\n"
        f"  note = {{Citations: {citations}}}\n"
        f"}}"
    )


def write_top_cited_bibliography(
    papers: list[dict[str, Any]],
    bibliography_path: Path,
    output_path: Path,
) -> list[str]:
    bibtex_entries = load_bibtex_entries(
        bibliography_path
    )

    matched_keys: list[str] = []
    generated_entries: list[str] = []

    for paper in papers:
        title = str(paper.get("title") or "")
        citations = int(paper.get("citations") or 0)

        match, score = find_matching_bibtex_entry(
            title,
            bibtex_entries,
        )

        if match is None:
            print(
                (
                    "WARNING: No BibTeX match found for "
                    f"{title!r}. Best score: {score:.3f}"
                ),
                file=sys.stderr,
            )
            continue

        matched_keys.append(match["key"])
        paper["bibtex_key"] = match["key"]
        paper["bibtex_match_score"] = round(score, 3)

        generated_entries.append(
            add_citation_note_to_bibtex(
                match["entry"],
                citations,
            )
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if generated_entries:
        output_text = "\n\n".join(generated_entries) + "\n"
    else:
        output_text = (
            "% No top-cited publications matched the main bibliography.\n"
        )

    output_path.write_text(
        output_text,
        encoding="utf-8",
    )

    return matched_keys


def write_json(
    output_path: Path,
    data: dict[str, Any],
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
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

    temporary_path.replace(output_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch Google Scholar metrics through SerpAPI, "
            "write Jekyll JSON data, and generate a BibTeX file "
            "for the most-cited publications."
        )
    )

    parser.add_argument(
        "--scholar-id",
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("_data/scholar.json"),
    )

    parser.add_argument(
        "--top-papers",
        type=int,
        default=5,
        help="Number of most-cited papers to store",
    )

    parser.add_argument(
        "--bibliography",
        type=Path,
        default=Path("_bibliography/publications.bib"),
        help="Main BibTeX file used by Jekyll-Scholar",
    )

    parser.add_argument(
        "--top-cited-bibliography",
        type=Path,
        default=Path("_bibliography/top_cited.bib"),
        help="Generated BibTeX file for most-cited papers",
    )

    args = parser.parse_args()

    api_key = os.getenv("SERPAPI_KEY", "").strip()

    if not api_key:
        print(
            "ERROR: SERPAPI_KEY is not configured.",
            file=sys.stderr,
        )
        return 1

    try:
        data = fetch_serpapi_author(
            scholar_id=args.scholar_id,
            api_key=api_key,
            top_papers=args.top_papers,
        )

        matched_keys = write_top_cited_bibliography(
            papers=data.get("top_cited_papers", []),
            bibliography_path=args.bibliography,
            output_path=args.top_cited_bibliography,
        )

        data["top_cited_bibtex_keys"] = matched_keys
        data["top_cited_bibliography"] = str(
            args.top_cited_bibliography
        )

        write_json(
            args.output,
            data,
        )

    except Exception as error:
        print(
            f"ERROR: {error}",
            file=sys.stderr,
        )
        print(
            "The existing JSON and generated BibTeX files were not modified.",
            file=sys.stderr,
        )
        return 1

    print(f"Updated {args.output}")
    print(f"Updated {args.top_cited_bibliography}")
    print(f"Source: {data['source']}")
    print(f"Citations: {data['citations']}")
    print(f"h-index: {data['h_index']}")
    print(f"i10-index: {data['i10_index']}")
    print(
        "Matched BibTeX keys: "
        + ", ".join(data.get("top_cited_bibtex_keys", []))
    )

    print("Most cited papers:")

    for paper in data["top_cited_papers"]:
        bibtex_key = paper.get("bibtex_key", "unmatched")

        print(
            f"- {paper['citations']} citations: "
            f"{paper['title']} [{bibtex_key}]"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
