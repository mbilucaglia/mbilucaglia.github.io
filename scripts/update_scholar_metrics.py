#!/usr/bin/env python3
"""Fetch Google Scholar author metrics and save them as Jekyll JSON data."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup


METRIC_KEYS = {
    "citations": "citations",
    "h-index": "h_index",
    "i10-index": "i10_index",
}


def utc_timestamp() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )


def profile_url(scholar_id: str) -> str:
    """Return the public Google Scholar profile URL."""
    return (
        "https://scholar.google.com/citations"
        f"?user={scholar_id}&hl=en"
    )


def parse_integer(value: str) -> int:
    """Convert a formatted metric such as '1,234' into an integer."""
    digits = "".join(
        character
        for character in value
        if character.isdigit()
    )

    if not digits:
        raise ValueError(
            f"Could not parse an integer from {value!r}"
        )

    return int(digits)


def parse_google_scholar_html(
    html: str,
    scholar_id: str,
) -> dict[str, Any]:
    """Extract metrics from a Google Scholar author HTML page."""
    soup = BeautifulSoup(html, "html.parser")

    metrics_table = soup.select_one("#gsc_rsb_st")

    if metrics_table is None:
        raise ValueError(
            "Google Scholar metrics table was not found. "
            "Google may have returned a block, consent, or CAPTCHA page."
        )

    metrics: dict[str, Any] = {}

    for row in metrics_table.select("tr"):
        label_element = row.select_one("td.gsc_rsb_sc1")
        value_elements = row.select("td.gsc_rsb_std")

        if label_element is None or not value_elements:
            continue

        label = " ".join(
            label_element
            .get_text(" ", strip=True)
            .lower()
            .split()
        )

        output_key = METRIC_KEYS.get(label)

        if output_key is None:
            continue

        metrics[output_key] = parse_integer(
            value_elements[0].get_text(" ", strip=True)
        )

        if len(value_elements) > 1:
            metrics[f"{output_key}_recent"] = parse_integer(
                value_elements[1].get_text(" ", strip=True)
            )

    required_keys = [
        "citations",
        "h_index",
        "i10_index",
    ]

    missing_keys = [
        key
        for key in required_keys
        if key not in metrics
    ]

    if missing_keys:
        raise ValueError(
            "Google Scholar page is missing metrics: "
            + ", ".join(missing_keys)
        )

    headings = [
        element.get_text(" ", strip=True)
        for element in metrics_table.select("thead th")
    ]

    recent_period = (
        headings[2]
        if len(headings) >= 3
        else None
    )

    name_element = soup.select_one("#gsc_prf_in")

    metrics.update(
        {
            "scholar_id": scholar_id,
            "profile_url": profile_url(scholar_id),
            "name": (
                name_element.get_text(" ", strip=True)
                if name_element
                else None
            ),
            "recent_period": recent_period,
            "source": "Google Scholar",
            "updated_at": utc_timestamp(),
        }
    )

    return metrics


def fetch_google_scholar_directly(
    scholar_id: str,
    attempts: int = 3,
) -> dict[str, Any]:
    """Try retrieving the public Scholar profile directly."""
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

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    errors: list[str] = []

    with requests.Session() as session:
        session.headers.update(headers)

        for url in urls:
            for attempt in range(1, attempts + 1):
                try:
                    response = session.get(
                        url,
                        timeout=30,
                    )

                    response.raise_for_status()

                    return parse_google_scholar_html(
                        response.text,
                        scholar_id,
                    )

                except (
                    requests.RequestException,
                    ValueError,
                ) as error:
                    errors.append(
                        f"{url}, attempt {attempt}: {error}"
                    )

                    if attempt < attempts:
                        time.sleep(attempt * 2)

    raise RuntimeError(
        "Direct Google Scholar retrieval failed:\n"
        + "\n".join(errors)
    )


def extract_serpapi_metrics(
    payload: dict[str, Any],
    scholar_id: str,
) -> dict[str, Any]:
    """Extract metrics from a SerpAPI Scholar Author response."""
    api_error = payload.get("error")

    if api_error:
        raise ValueError(
            f"SerpAPI returned an error: {api_error}"
        )

    search_status = (
        payload
        .get("search_metadata", {})
        .get("status")
    )

    if search_status == "Error":
        raise ValueError(
            "SerpAPI reported an unsuccessful search"
        )

    cited_by = payload.get("cited_by", {})

    if not isinstance(cited_by, dict):
        raise ValueError(
            "SerpAPI response does not contain cited_by data"
        )

    table = cited_by.get("table", [])

    if not isinstance(table, list):
        raise ValueError(
            "SerpAPI cited_by.table is not a list"
        )

    metrics: dict[str, Any] = {}
    recent_period: str | None = None

    api_to_output_key = {
        "citations": "citations",
        "h_index": "h_index",
        "i10_index": "i10_index",
    }

    for row in table:
        if not isinstance(row, dict):
            continue

        for api_key, values in row.items():
            output_key = api_to_output_key.get(api_key)

            if output_key is None:
                continue

            if not isinstance(values, dict):
                continue

            all_value = values.get("all")

            if all_value is None:
                continue

            metrics[output_key] = int(all_value)

            recent_keys = [
                key
                for key in values
                if key.startswith("since_")
            ]

            if recent_keys:
                recent_key = sorted(recent_keys)[-1]

                metrics[f"{output_key}_recent"] = int(
                    values[recent_key]
                )

                recent_year = recent_key.removeprefix(
                    "since_"
                )

                recent_period = f"Since {recent_year}"

    required_keys = [
        "citations",
        "h_index",
        "i10_index",
    ]

    missing_keys = [
        key
        for key in required_keys
        if key not in metrics
    ]

    if missing_keys:
        raise ValueError(
            "SerpAPI response is missing metrics: "
            + ", ".join(missing_keys)
        )

    author = payload.get("author", {})

    if not isinstance(author, dict):
        author = {}

    metrics.update(
        {
            "scholar_id": scholar_id,
            "profile_url": profile_url(scholar_id),
            "name": author.get("name"),
            "recent_period": recent_period,
            "source": "Google Scholar via SerpAPI",
            "updated_at": utc_timestamp(),
        }
    )

    return metrics


def fetch_serpapi_metrics(
    scholar_id: str,
    api_key: str,
) -> dict[str, Any]:
    """Retrieve Google Scholar metrics through SerpAPI."""
    response = requests.get(
        "https://serpapi.com/search.json",
        params={
            "engine": "google_scholar_author",
            "author_id": scholar_id,
            "hl": "en",
            "api_key": api_key,
        },
        timeout=60,
    )

    response.raise_for_status()

    try:
        payload = response.json()
    except requests.JSONDecodeError as error:
        raise ValueError(
            "SerpAPI did not return valid JSON"
        ) from error

    return extract_serpapi_metrics(
        payload,
        scholar_id,
    )


def write_json_atomically(
    output_path: Path,
    metrics: dict[str, Any],
) -> None:
    """Write JSON without risking a partially written output file."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            metrics,
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
            "Retrieve Google Scholar author metrics and "
            "write them as Jekyll JSON data."
        )
    )

    parser.add_argument(
        "--scholar-id",
        required=True,
        help="Google Scholar author identifier",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("_data/scholar.json"),
        help="Destination JSON file",
    )

    arguments = parser.parse_args()

    direct_error: Exception | None = None

    try:
        print(
            "Trying direct Google Scholar retrieval..."
        )

        metrics = fetch_google_scholar_directly(
            arguments.scholar_id
        )

    except Exception as error:
        direct_error = error

        print(
            f"Direct retrieval failed:\n{error}",
            file=sys.stderr,
        )

        serpapi_key = os.getenv(
            "SERPAPI_KEY",
            "",
        ).strip()

        if not serpapi_key:
            print(
                "ERROR: SERPAPI_KEY is not configured.",
                file=sys.stderr,
            )

            print(
                "The existing JSON file was not modified.",
                file=sys.stderr,
            )

            return 1

        try:
            print(
                "Trying SerpAPI fallback..."
            )

            metrics = fetch_serpapi_metrics(
                arguments.scholar_id,
                serpapi_key,
            )

        except Exception as serpapi_error:
            print(
                "ERROR: Both retrieval methods failed.",
                file=sys.stderr,
            )

            print(
                f"Direct Google Scholar error:\n{direct_error}",
                file=sys.stderr,
            )

            print(
                f"SerpAPI error:\n{serpapi_error}",
                file=sys.stderr,
            )

            print(
                "The existing JSON file was not modified.",
                file=sys.stderr,
            )

            return 1

    write_json_atomically(
        arguments.output,
        metrics,
    )

    print(f"Updated {arguments.output}")
    print(f"Source: {metrics['source']}")
    print(f"Citations: {metrics['citations']}")
    print(f"h-index: {metrics['h_index']}")
    print(f"i10-index: {metrics['i10_index']}")
    print(f"Updated at: {metrics['updated_at']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
