#!/usr/bin/env python3
"""Create 1031351_extractions.json from 1031351_actual_results.json (simplified format)."""

import json
from pathlib import Path

def main():
    base = Path(__file__).resolve().parent.parent
    actual_path = base / "1031351_actual_results.json"
    out_path = base / "1031351_extractions.json"

    with open(actual_path, encoding="utf-8") as f:
        data = json.load(f)

    citations = data.get("citations", [])
    extractions = []
    for c in citations:
        extractions.append({
            "citation": c.get("citation", ""),
            "extracted_case_name": c.get("extracted_case_name") or c.get("case_name") or c.get("canonical_name") or "N/A",
            "extracted_date": c.get("extracted_date") or c.get("canonical_date") or "N/A",
            "start_index": c.get("start_index"),
            "end_index": c.get("end_index"),
        })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(extractions, f, indent=2)

    print(f"Wrote {len(extractions)} entries to {out_path}")

if __name__ == "__main__":
    main()
