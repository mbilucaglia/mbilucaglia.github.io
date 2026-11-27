#!/usr/bin/env python3
"""Refresh author metrics in a temporary CV checkout; never push to MyCV."""
import argparse
import json
import os
import re
from pathlib import Path

import requests


def integer(value):
    if isinstance(value, bool) or not re.fullmatch(r"\d+", str(value)):
        raise ValueError("Invalid metric")
    return int(value)


def scopus():
    key = os.getenv("ELSEVIER_API_KEY")
    if not key:
        raise ValueError("Missing Elsevier key")
    headers = {"Accept": "application/json", "X-ELS-APIKey": key}
    if os.getenv("ELSEVIER_INSTTOKEN"):
        headers["X-ELS-Insttoken"] = os.environ["ELSEVIER_INSTTOKEN"]
    response = requests.get(
        "https://api.elsevier.com/content/author/author_id/57188983512",
        headers=headers,
        params={"view": "METRICS"},
        timeout=30,
    )
    response.raise_for_status()
    record = response.json()["author-retrieval-response"][0]
    core = record["coredata"]
    if core["dc:identifier"] != "AUTHOR_ID:57188983512":
        raise ValueError("Unexpected Scopus author")
    return {
        "Citations": integer(core["citation-count"]),
        "Documents": integer(core["document-count"]),
        "h-index": integer(record["h-index"]),
    }


def replace_section(text, section, metrics):
    pattern = r"(\\subsection\*\{" + re.escape(section) + r"\}.*?)(?=\\subsection\*|\Z)"
    match = re.search(pattern, text, re.S)
    if not match:
        raise ValueError("Missing section")
    block = match.group(1)
    for label, value in metrics.items():
        field = r"(\\item\s+\\textbf\{" + re.escape(label) + r"\}:\s*)[^\r\n]+"
        block, count = re.subn(field, lambda m: m[1] + str(value), block)
        if count != 1:
            raise ValueError("Unexpected metric layout")
    return text[:match.start()] + block + text[match.end():]


def scholar(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    period = re.fullmatch(r"Since (\d{4})", data["recent_period"])
    if data["scholar_id"] != "RvAqXUIAAAAJ" or not period:
        raise ValueError("Unexpected Scholar profile or period")
    return {
        label: f"{integer(data[key])}--{integer(data[key + '_recent'])} (All--since {period[1]})"
        for label, key in [
            ("Citations", "citations"), ("h-index", "h_index"), ("i10-index", "i10_index")
        ]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cv", type=Path, required=True)
    parser.add_argument("--scholar", type=Path, default=Path("_data/scholar.json"))
    parser.add_argument("--refresh-scopus", action="store_true")
    parser.add_argument("--scopus-cache", type=Path)
    parser.add_argument("--require-scopus", action="store_true")
    args = parser.parse_args()
    text = args.cv.read_text(encoding="utf-8")
    sources = [("Google Scholar", lambda: scholar(args.scholar))]
    def scopus_metrics():
        if args.refresh_scopus:
            try:
                metrics = scopus()
                if args.scopus_cache:
                    args.scopus_cache.parent.mkdir(parents=True, exist_ok=True)
                    args.scopus_cache.write_text(json.dumps(metrics), encoding="utf-8")
                return metrics
            except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, OSError) as exc:
                detail = type(exc).__name__
                if isinstance(exc, requests.HTTPError) and exc.response is not None:
                    detail = f"HTTP {exc.response.status_code}"
                    try:
                        payload = exc.response.json()
                        status = payload.get("service-error", {}).get("status", {})
                        code = status.get("statusCode", "")
                        if re.fullmatch(r"[A-Z0-9_]{1,64}", str(code)):
                            detail += f" ({code})"
                    except (ValueError, TypeError, AttributeError):
                        pass
                if args.require_scopus:
                    raise RuntimeError("Scopus live validation failed: " + detail) from None
                print(f"::warning::Scopus refresh failed ({detail}); trying previous metrics")
        if args.scopus_cache and args.scopus_cache.exists():
            data = json.loads(args.scopus_cache.read_text(encoding="utf-8"))
            return {label: integer(data[label]) for label in ("Citations", "Documents", "h-index")}
        raise ValueError("No cached Scopus metrics")

    if args.refresh_scopus or args.scopus_cache:
        sources.append(("Scopus", scopus_metrics))
    for name, fetch in sources:
        try:
            text = replace_section(text, name, fetch())
            print(f"{name}: updated")
        except requests.HTTPError as exc:
            print(f"::warning::{name}: HTTP {exc.response.status_code}; keeping CV values")
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, OSError) as exc:
            print(f"::warning::{name}: {type(exc).__name__}; keeping CV values")
    args.cv.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
