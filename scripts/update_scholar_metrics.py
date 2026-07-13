#!/usr/bin/env python3
"""Fetch Google Scholar author metrics and most-cited papers via SerpAPI."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
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

            total = values.get("all")

            recent_value = None
            recent_period = None

            for value_key, value in values.items():
                if value_key == "all":
                    continue

                if value_key.startswith("since_"):
                    recent_value = value
                    recent_period = (
                        "Since "
                        + value_key.removeprefix("since_")
                    )
                    break

            return (
                int(total) if total is not None else None,
                int(recent_value) if recent_value is not None else None,
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
        citations = int(cited_by.get("value") or 0)

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
            # SerpAPI returns articles sorted by citation count by default.
            # num can be up to 100.
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
    parser = argparse.ArgumentParser()

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
            "The existing JSON file was not modified.",
            file=sys.stderr,
        )
        return 1

    print(f"Updated {args.output}")
    print(f"Source: {data['source']}")
    print(f"Citations: {data['citations']}")
    print(f"h-index: {data['h_index']}")
    print(f"i10-index: {data['i10_index']}")

    print("Most cited papers:")

    for paper in data["top_cited_papers"]:
        print(
            f"- {paper['citations']} citations: {paper['title']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
