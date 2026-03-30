#!/usr/bin/env python3
"""
Compare citation counts with and without the P.3d bleed filter.
Usage:
  python scripts/compare_citation_counts.py [path/to/document.pdf]
  python scripts/compare_citation_counts.py --text "path/to/extracted.txt"

If no path given, uses 1031351.pdf from project root.
"""

import json
import os
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


def extract_text(path: Path) -> str:
    """Extract text from PDF using UnifiedTextExtractor."""
    from src.unified_text_extractor import extract_text_from_file_unified
    text, _ = extract_text_from_file_unified(str(path), verbose=False)
    return text or ""


def run_extraction(text: str, disable_filter: bool) -> int:
    """Run unified extraction and return citation count."""
    env_key = "DISABLE_P3D_BLEED_FILTER"
    old_val = os.environ.get(env_key)
    try:
        os.environ[env_key] = "1" if disable_filter else "0"
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        import asyncio
        proc = UnifiedCitationProcessorV2()
        result = asyncio.get_event_loop().run_until_complete(proc.process_text(text))
        citations = result.get("citations") or []
        return len(citations)
    finally:
        if old_val is not None:
            os.environ[env_key] = old_val
        elif env_key in os.environ:
            del os.environ[env_key]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--text":
        if len(sys.argv) < 3:
            print("Usage: --text path/to/file.txt")
            return 1
        path = Path(sys.argv[2])
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        pdf_path = Path(sys.argv[1]) if len(sys.argv) > 1 else _project_root / "1031351.pdf"
        if not pdf_path.exists():
            print(f"File not found: {pdf_path}")
            return 1
        print(f"Extracting text from {pdf_path}...")
        text = extract_text(pdf_path)
        if not text:
            print("No text extracted")
            return 1

    print(f"Text length: {len(text):,} chars\n")

    print("Running extraction WITH P.3d bleed filter...")
    count_with = run_extraction(text, disable_filter=False)
    print(f"  Citations: {count_with}")

    print("Running extraction WITHOUT P.3d bleed filter...")
    count_without = run_extraction(text, disable_filter=True)
    print(f"  Citations: {count_without}")

    diff = count_without - count_with
    print(f"\nDifference: {diff} citations")
    if diff > 0:
        print(f"  Filter removed {diff} citation(s)")
    elif diff < 0:
        print(f"  (Unexpected: filter added {-diff})")

    out = _project_root / "citation_count_comparison.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {"with_filter": count_with, "without_filter": count_without, "difference": diff},
            f,
            indent=2,
        )
    print(f"\nSaved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
