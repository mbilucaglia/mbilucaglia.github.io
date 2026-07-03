from __future__ import annotations

import argparse
import json
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


def parse_integer(value: str) -> int:
    digits = "".join(character for character in value if character.isdigit())

    if not digits:
        raise ValueError(f"Could not parse integer from {value!r}")

    return int(digits)


def parse_scholar_page(
    html: str,
    scholar_id: str,
) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    metrics_table = soup.select_one("#gsc_rsb_st")

    if metrics_table is None:
        raise ValueError(
            "The Google Scholar metrics table was not found. "
            "Google may have returned a block, consent, or CAPTCHA page."
        )

    metrics: dict[str, Any] = {}

    for row in metrics_table.select("tr"):
        label_element = row.select_one("td.gsc_rsb_sc1")
        value_elements = row.select("td.gsc_rsb_std")

        if label_element is None or not value_elements:
            continue

        label = " ".join(
            label_element.get_text(" ", strip=True).lower().split()
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
            "Missing metrics: " + ", ".join(missing_keys)
        )

    headings = [
        element.get_text(" ", strip=True)
        for element in metrics_table.select("thead th")
    ]

    recent_period = headings[2] if len(headings) >= 3 else None

    profile_name_element = soup.select_one("#gsc_prf_in")

    profile_name = (
        profile_name_element.get_text(" ", strip=True)
        if profile_name_element
        else None
    )

    metrics.update(
        {
            "scholar_id": scholar_id,
            "profile_url": (
                "https://scholar.google.com/citations"
                f"?user={scholar_id}&hl=en"
            ),
            "name": profile_name,
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


def download_scholar_page(
    scholar_id: str,
) -> str:
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
        "Accept-Language": "en-US,en;q=0.9",
    }

    errors: list[str] = []

    with requests.Session() as session:
        session.headers.update(headers)

        for url in urls:
            for attempt in range(1, 4):
                try:
                    response = session.get(
                        url,
                        timeout=30,
                    )

                    response.raise_for_status()

                    if "gsc_rsb_st" not in response.text:
                        raise ValueError(
                            "response does not contain the metrics table"
                        )

                    print(f"Downloaded metrics from {url}")

                    return response.text

                except (requests.RequestException, ValueError) as error:
                    errors.append(
                        f"{url}, attempt {attempt}: {error}"
                    )

                    if attempt < 3:
                        time.sleep(attempt * 2)

    raise RuntimeError(
        "Google Scholar retrieval failed:\n"
        + "\n".join(errors)
    )


def write_json(
    output_path: Path,
    metrics: dict[str, Any],
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
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--scholar-id",
        required=True,
        help="Google Scholar profile identifier",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("_data/scholar.json"),
        help="Destination JSON file",
    )

    arguments = parser.parse_args()

    try:
        html = download_scholar_page(
            arguments.scholar_id
        )

        metrics = parse_scholar_page(
            html,
            arguments.scholar_id,
        )

        write_json(
            arguments.output,
            metrics,
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

    print(f"Updated {arguments.output}")
    print(f"Citations: {metrics['citations']}")
    print(f"h-index: {metrics['h_index']}")
    print(f"i10-index: {metrics['i10_index']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
