#!/usr/bin/env python3
"""
Run unified extraction + clustering (no CourtListener verification) on NAAG amicus PDFs.

Default directory: ``<repo>/downloaded_briefs/naag_amicus/`` (populate with
``python scripts/download_naag_amicus_briefs.py``).

Usage::

    python scripts/smoke_naag_amicus_briefs.py
    python scripts/smoke_naag_amicus_briefs.py --max-files 5
    python scripts/smoke_naag_amicus_briefs.py --dir D:/briefs/naag --json-out runs/naag_smoke.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = REPO_ROOT / "downloaded_briefs" / "naag_amicus"

# Amicus merits briefs: expect substantial text and usually many cites when PDF text layer is good.
MIN_TEXT_WARN = 500
MIN_CITES_WARN = 1


async def _run_pipeline(text: str) -> dict:
    from src.unified_processing_pipeline import process_citations_unified

    return await process_citations_unified(
        text,
        enable_verification=False,
        enable_parallel_verification=False,
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Smoke-test pipeline on NAAG amicus PDFs.")
    p.add_argument("--dir", type=Path, default=DEFAULT_DIR, help="Folder containing PDFs")
    p.add_argument("--max-files", type=int, default=0, help="Limit PDF count (0 = all)")
    p.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write summary JSON to this path",
    )
    args = p.parse_args(argv)

    d = args.dir.resolve()
    if not d.is_dir():
        print(f"Directory not found: {d}", file=sys.stderr)
        print("Run: python scripts/download_naag_amicus_briefs.py", file=sys.stderr)
        return 2

    pdfs = sorted(d.glob("*.pdf"))
    if args.max_files and args.max_files > 0:
        pdfs = pdfs[: args.max_files]
    if not pdfs:
        print(f"No PDFs under {d}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(REPO_ROOT))
    os.chdir(REPO_ROOT)
    from src.unified_text_extractor import extract_text_from_file_unified

    rows: list[dict] = []
    warnings = 0

    print(f"Processing {len(pdfs)} PDF(s) from {d}\n")

    for pdf_path in pdfs:
        text, method = extract_text_from_file_unified(str(pdf_path), verbose=False)
        result = asyncio.run(_run_pipeline(text))
        citations = result.get("citations") or []
        clusters = result.get("clusters") or []
        n_cit = len(citations) if isinstance(citations, list) else 0
        n_cl = len(clusters) if isinstance(clusters, list) else 0
        row = {
            "file": pdf_path.name,
            "text_chars": len(text),
            "extract_method": method,
            "citation_count": n_cit,
            "cluster_count": n_cl,
        }
        rows.append(row)
        flag = ""
        if len(text) < MIN_TEXT_WARN:
            flag = " [WARN: very little text — scanned PDF?]"
            warnings += 1
        elif n_cit < MIN_CITES_WARN and len(text) >= 4000:
            flag = " [WARN: long text but 0 citations]"
            warnings += 1
        print(
            f"{pdf_path.name}: text={len(text)} cites={n_cit} clusters={n_cl} ({method}){flag}"
        )

    print()
    if warnings:
        print(f"Warnings: {warnings} file(s) look suspicious (see flags above).")

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Wrote {args.json_out.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
