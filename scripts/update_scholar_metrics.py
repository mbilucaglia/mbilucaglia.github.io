#!/usr/bin/env python3
"""Fetch public Google Scholar author metrics and write them as Jekyll data."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


METRIC_KEYS = {
    "citations": "citations",
    "h-index": "h_index",
    "i10-index": "i10_index",
}


def parse_int(value: str) -> int:
    digits = "".join(character for character in value if character.isdigit())

    if not digits:
        raise ValueError(f"Expected an integer metric, got {value!r}")

    return int(digits)


def parse_google_scholar_html(
    html: str,
    scholar_id: str,
) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    table = soup.select_one("#gsc_rsb_st")

    if table is None:
        raise ValueError("Google Scholar metrics table was not found")

    metrics: dict[str, Any] = {}

    for row in table.select("tr"):
        label_cell = row.select_one("td.gsc_rsb_sc1")
        values = row.select("td.gsc_rsb_std")

        if label_cell is None or not values:
            continue

        label = " ".join(
            label_cell.get_text(" ", strip=True).lower().split()
        )

        key = METRIC_KEYS.get(label)

        if key is None:
            continue

        metrics[key] = parse_int(
            values[0].get_text(" ", strip=True)
        )

        if len(values) > 1:
            metrics[f"{key}_recent"] = parse_int(
                values[1].get_text(" ", strip=True)
            )

    missing = [
        key
        for key in METRIC_KEYS.values()
        if key not in metrics
    ]

    if missing:
        raise ValueError(
            f"Missing Google Scholar metrics: {', '.join(missing)}"
        )

    headings = [
        cell.get_text(" ", strip=True)
        for cell in table.select("thead th")
    ]

    recent_period = headings[2] if len(headings) >= 3 else None
    profile_name = soup.select_one("#gsc_prf_in")

    metrics.update(
        {
            "scholar_id": scholar_id,
            "profile_url": (
                "https://scholar.google.com/citations"
                f"?user={scholar_id}&hl=en"
            ),
            "name": (
                profile_name.get_text(" ", strip=True)
                if profile_name
                else None
            ),
            "recent_period": recent_period,
            "source": "Google Scholar",
            "updated_at": (
                datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
            ),
        }
    )

    return metrics


def fetch_google_scholar_html(
    scholar_id: str,
    attempts: int = 3,
) -> str:
    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    urls = [
        (
            "https://scholar.google.com/citations"
            f"?user={scholar_id}&hl=en"
        ),
        (
            "https://scholar.google.it/citations"
            f"?user={scholar_id}&hl=en"
        ),
    ]

    errors: list[str] = []

    for url in urls:
        for attempt in range(1, attempts + 1):
            try:
                response = session.get(url, timeout=30)
                response.raise_for_status()

                if "gsc_rsb_st" not in response.text:
                    raise ValueError(
                        "response did not contain the metrics table"
                    )

                return response.text

            except (requests.RequestException, ValueError) as exc:
                errors.append(
                    f"{url} attempt {attempt}: {exc}"
                )

                if attempt < attempts:
                    time.sleep(attempt * 2)

    raise RuntimeError("; ".join(errors))


def fetch_serpapi_metrics(
    scholar_id: str,
    api_key: str,
) -> dict[str, Any]:
    query = urlencode(
        {
            "engine": "google_scholar_author",
            "author_id": scholar_id,
            "hl": "en",
            "api_key": api_key,
        }
    )

    response = requests.get(
        f"https://serpapi.com/search.json?{query}",
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    metrics: dict[str, Any] = {}
    recent_period = None

    for row in payload.get("cited_by", {}).get("table", []):
        if not isinstance(row, dict) or len(row) != 1:
            continue

        api_name, values = next(iter(row.items()))

        output_key = {
            "citations": "citations",
            "h_index": "h_index",
            "i10_index": "i10_index",
        }.get(api_name)

        if (
            output_key is None
            or not isinstance(values, dict)
            or "all" not in values
        ):
            continue

        metrics[output_key] = int(values["all"])

        recent_keys = [
            key
            for key in values
            if key != "all"
        ]

        if recent_keys:
            recent_key = recent_keys[0]

            metrics[f"{output_key}_recent"] = int(
                values[recent_key]
            )

            recent_period = (
                recent_key
                .replace("since_", "Since ")
                .replace("_", " ")
            )

    missing = [
        key
        for key in METRIC_KEYS.values()
        if key not in metrics
    ]

    if missing:
        raise ValueError(
            "SerpAPI response is missing metrics: "
            f"{', '.join(missing)}"
        )

    author = payload.get("author", {})

    metrics.update(
        {
            "scholar_id": scholar_id,
            "profile_url": (
                "https://scholar.google.com/citations"
                f"?user={scholar_id}&hl=en"
            ),
            "name": author.get("name"),
            "recent_period": recent_period,
            "source": "Google Scholar via SerpAPI",
            "updated_at": (
                datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
            ),
        }
    )

    return metrics


def write_json(
    output: Path,
    payload: dict[str, Any],
) -> None:
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def keep_existing_metrics(
    output: Path,
    message: str,
) -> int:
    print(message, file=sys.stderr)

    if output.exists():
        print(
            f"Keeping existing metrics in {output}.",
            file=sys.stderr,
        )

        return 0

    print(
        "No existing metrics file is available.",
        file=sys.stderr,
    )

    return 1


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

    args = parser.parse_args()

    try:
        html = fetch_google_scholar_html(
            args.scholar_id
        )

        metrics = parse_google_scholar_html(
            html,
            args.scholar_id,
        )

    except Exception as direct_error:
        serpapi_key = os.getenv(
            "SERPAPI_KEY",
            "",
        ).strip()

        if not serpapi_key:
            return keep_existing_metrics(
                args.output,
                f"Google Scholar fetch failed: {direct_error}",
            )

        try:
            metrics = fetch_serpapi_metrics(
                args.scholar_id,
                serpapi_key,
            )

        except Exception as fallback_error:
            return keep_existing_metrics(
                args.output,
                (
                    "Google Scholar fetch failed: "
                    f"{direct_error}\n"
                    "SerpAPI fallback failed: "
                    f"{fallback_error}"
                ),
            )

    write_json(
        args.output,
        metrics,
    )

    print(f"Updated {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
