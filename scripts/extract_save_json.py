#!/usr/bin/env python3
"""
Extract citations from a PDF and save result to JSON.
Runs extraction only - no verification. Use for comparison fixtures.

Usage:
  python scripts/extract_save_json.py <pdf_path> [output.json]

If output path omitted, writes to <pdf_stem>_actual.json in project root.

OOM note: Runs in a single process. For large PDFs, run extraction via API
and save the response manually, then use compare_extraction_to_expected.py.
"""

import asyncio
import json
import sys
from datetime import date, datetime
from pathlib import Path


def _json_serial(obj):
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_save_json.py <pdf_path> [output.json]")
        sys.exit(1)

    base = Path(__file__).resolve().parent.parent
    pdf_path = Path(sys.argv[1])
    if not pdf_path.is_absolute():
        pdf_path = base / pdf_path

    if not pdf_path.exists():
        print(f"PDF not found: {pdf_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
    else:
        out_path = base / f"{pdf_path.stem}_actual.json"

    if not out_path.is_absolute():
        out_path = base / out_path

    print(f"Extracting text from {pdf_path.name}...")
    from src.unified_text_extractor import extract_text_from_file_unified

    text, method = extract_text_from_file_unified(str(pdf_path), verbose=False)
    if not text or len(text.strip()) < 100:
        print("ERROR: Text extraction returned empty or very short text.")
        sys.exit(1)

    print(f"Extracted {len(text):,} chars using {method}. Running citation pipeline...")

    from src.unified_processing_pipeline import process_citations_unified

    result = asyncio.run(
        process_citations_unified(
            text,
            enable_verification=False,
            enable_parallel_verification=False,
        )
    )

    # Keep only fields needed for comparison
    out = {
        "citations": result.get("citations", []),
        "clusters": result.get("clusters", []),
        "metadata": result.get("metadata", {}),
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=_json_serial)

    print(f"Saved to {out_path}")
    print(f"  Citations: {len(out['citations'])}")
    print(f"  Clusters:  {len(out['clusters'])}")


if __name__ == "__main__":
    main()
