#!/usr/bin/env python3
"""
Extract citations from PDF or text and save to JSON.

Designed for OOM safety: run steps separately.
  Step 1 (text only):  python run_extract_and_save.py --text-only doc.pdf doc_text.txt
  Step 2 (citations): python run_extract_and_save.py --from-text doc_text.txt doc_result.json
  Full run:            python run_extract_and_save.py doc.pdf doc_result.json

Usage:
  python scripts/run_extract_and_save.py <pdf_path> <output_json>
  python scripts/run_extract_and_save.py --text-only <pdf_path> <output_txt>
  python scripts/run_extract_and_save.py --from-text <text_path> <output_json>
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def _extract_text(pdf_path: Path) -> str:
    """Extract text from PDF. May OOM on very large PDFs."""
    from src.unified_text_extractor import extract_text_from_file_unified

    text, _ = extract_text_from_file_unified(str(pdf_path), verbose=False)
    return text


def _run_pipeline(text: str, enable_verification: bool = False) -> dict:
    """Run citation pipeline on text. Verification disabled by default for speed."""
    from src.unified_processing_pipeline import process_citations_unified

    return asyncio.run(
        process_citations_unified(
            text,
            enable_verification=enable_verification,
            enable_parallel_verification=False,
        )
    )


def main():
    parser = argparse.ArgumentParser(description="Extract citations and save to JSON")
    parser.add_argument("input", type=Path, help="PDF path or text path (with --from-text)")
    parser.add_argument("output", type=Path, help="Output JSON or TXT path")
    parser.add_argument("--text-only", action="store_true", help="Only extract text from PDF, save to file")
    parser.add_argument("--from-text", action="store_true", help="Input is text file, run pipeline on it")
    parser.add_argument("--verify", action="store_true", help="Enable verification (slower, may hit API limits)")
    args = parser.parse_args()

    if args.text_only:
        print(f"Extracting text from {args.input}...")
        text = _extract_text(args.input)
        args.output.write_text(text, encoding="utf-8")
        print(f"Saved {len(text):,} chars to {args.output}")
        return 0

    if args.from_text:
        print(f"Loading text from {args.input}...")
        text = args.input.read_text(encoding="utf-8")
        print(f"Running pipeline on {len(text):,} chars...")
    else:
        print(f"Extracting text from {args.input}...")
        text = _extract_text(args.input)
        print(f"Running pipeline on {len(text):,} chars...")

    result = _run_pipeline(text, enable_verification=args.verify)
    args.output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(f"Saved {len(result.get('clusters', []))} clusters to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
