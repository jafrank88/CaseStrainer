#!/usr/bin/env python3
"""
Fetch Supreme Court brief listings from the U.S. Department of Justice OSG site.

Source index page: https://www.justice.gov/osg/supreme-court-briefs

This script downloads HTML table rows only (metadata + PDF links). PDF bodies are
optional (--download-pdfs). Be polite: use small --pages, --sleep, and a descriptive
User-Agent (set in src.utils.justice_osg_brief_listing).

Examples
--------
  python scripts/fetch_osg_supreme_court_brief_index.py --pages 1 --out data/justice_osg/index_page0.json
  python scripts/fetch_osg_supreme_court_brief_index.py --pages 3 --sleep 2.0 --out data/justice_osg/index.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx

from src.utils.justice_osg_brief_listing import (
    DEFAULT_FETCH_UA,
    LIST_URL,
    media_id_from_pdf_url,
    parse_brief_table_rows,
)


def _safe_filename(s: str) -> str:
    s = re.sub(r"[^\w.\-]+", "_", s, flags=re.ASCII)
    return s[:180] if len(s) > 180 else s


def fetch_listing_page(page: int, client: httpx.Client) -> str:
    params = {} if page == 0 else {"page": str(page)}
    r = client.get(LIST_URL, params=params)
    r.raise_for_status()
    return r.text


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fetch DOJ OSG Supreme Court brief index rows.")
    p.add_argument("--pages", type=int, default=1, help="Number of listing pages to fetch (default 1).")
    p.add_argument(
        "--start-page",
        type=int,
        default=0,
        help="First Drupal page index (0-based, default 0).",
    )
    p.add_argument("--out", type=Path, help="Write combined JSON to this path.")
    p.add_argument("--sleep", type=float, default=1.5, help="Seconds between HTTP requests.")
    p.add_argument(
        "--download-pdfs",
        type=Path,
        default=None,
        metavar="DIR",
        help="If set, download each PDF referenced in fetched rows into this directory.",
    )
    p.add_argument("--dry-run", action="store_true", help="Fetch and print counts only.")
    args = p.parse_args(argv)

    if args.pages < 1:
        print("--pages must be >= 1", file=sys.stderr)
        return 2

    headers = {"User-Agent": DEFAULT_FETCH_UA}
    all_rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None]] = set()

    with httpx.Client(headers=headers, timeout=60.0, follow_redirects=True) as client:
        for i in range(args.pages):
            page_idx = args.start_page + i
            if i > 0:
                time.sleep(max(0.0, args.sleep))
            html = fetch_listing_page(page_idx, client)
            batch = parse_brief_table_rows(html)
            for row in batch:
                key = (row["docket"], row.get("pdf_url"))
                if key in seen:
                    continue
                seen.add(key)
                row["listing_page"] = page_idx
                all_rows.append(row)

            if args.dry_run:
                print(f"page {page_idx}: {len(batch)} table rows")

        if args.dry_run:
            print(json.dumps({"entry_count": len(all_rows)}, indent=2))
            return 0

        if args.download_pdfs is not None:
            args.download_pdfs.mkdir(parents=True, exist_ok=True)
            for row in all_rows:
                pdf_url = row.get("pdf_url")
                if not pdf_url:
                    continue
                time.sleep(max(0.0, args.sleep))
                pr = client.get(pdf_url)
                pr.raise_for_status()
                stem = media_id_from_pdf_url(pdf_url) or _safe_filename(row["docket"])
                fn = args.download_pdfs / f"{stem}_{_safe_filename(row['docket'])}.pdf"
                fn.write_bytes(pr.content)

    payload: dict[str, Any] = {
        "source": LIST_URL,
        "generator": "scripts/fetch_osg_supreme_court_brief_index.py",
        "entry_count": len(all_rows),
        "entries": all_rows,
    }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {len(all_rows)} entries to {args.out}")
    else:
        text = json.dumps(payload, indent=2)
        print(text[:8000])
        if len(text) > 8000:
            print("\n... truncated; use --out PATH for full JSON", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
