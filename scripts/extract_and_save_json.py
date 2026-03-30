#!/usr/bin/env python3
"""
Extract citations from a PDF and save result to JSON.
Run this separately from comparison to avoid OOM on large PDFs.

Usage:
  python scripts/extract_and_save_json.py 1033397.pdf
  python scripts/extract_and_save_json.py 1033397.pdf -o 1033397_actual.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("-o", "--output", help="Output JSON path (default: <stem>_actual.json)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or (pdf_path.stem + "_actual.json")
    if not Path(output_path).is_absolute():
        output_path = project_root / output_path

    print(f"Extracting text from {pdf_path}...")
    from src.unified_text_extractor import extract_text_from_file_unified

    text, method = extract_text_from_file_unified(str(pdf_path), verbose=False)
    print(f"  Text: {len(text):,} chars ({method})")

    print("Running citation extraction...")
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

    processor = UnifiedCitationProcessorV2()
    result = asyncio.run(processor.process_document_citations(text))

    citations = result.get("citations", [])
    clusters = result.get("clusters", [])
    print(f"  Citations: {len(citations)}, Clusters: {len(clusters)}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
