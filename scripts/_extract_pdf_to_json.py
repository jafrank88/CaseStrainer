#!/usr/bin/env python3
"""
Standalone extraction script - runs in subprocess to avoid OOM.
Extracts text from PDF, runs citation pipeline, saves result to JSON.

Usage: python _extract_pdf_to_json.py <pdf_path> <output_json_path>
"""

import asyncio
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python _extract_pdf_to_json.py <pdf_path> <output_json_path>")
        return 1

    pdf_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        return 1

    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

    # Step 1: Extract text (minimal imports)
    from src.unified_text_extractor import extract_text_from_file_unified

    print(f"Extracting text from {pdf_path}...")
    text, method = extract_text_from_file_unified(str(pdf_path), verbose=False)
    print(f"  Extracted {len(text):,} chars using {method}")

    if not text or len(text.strip()) < 100:
        print("Error: Insufficient text extracted")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"error": "Insufficient text extracted", "citations": [], "clusters": []}, f, indent=2)
        return 1

    # Step 2: Run pipeline (async)
    async def run():
        from src.unified_processing_pipeline import process_citations_unified

        return await process_citations_unified(text, enable_verification=True)

    print("Running citation pipeline...")
    result = asyncio.run(run())

    # Step 3: Extract serializable parts
    citations = result.get("citations", [])
    clusters = result.get("clusters", [])

    def to_serializable(obj):
        """Convert to JSON-serializable form."""
        if obj is None:
            return None
        if isinstance(obj, dict):
            return {k: to_serializable(v) for k, v in obj.items() if not callable(v)}
        if isinstance(obj, (list, tuple)):
            return [to_serializable(x) for x in obj]
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if hasattr(obj, "to_dict"):
            return to_serializable(obj.to_dict())
        if hasattr(obj, "__dict__"):
            return to_serializable(obj.__dict__)
        return str(obj)

    output = {
        "document_id": pdf_path.stem,
        "citations_count": len(citations),
        "clusters_count": len(clusters),
        "citations": to_serializable(citations),
        "clusters": to_serializable(clusters),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Saved {len(citations)} citations, {len(clusters)} clusters to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
