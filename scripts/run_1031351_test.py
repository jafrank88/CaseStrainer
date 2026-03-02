#!/usr/bin/env python3
"""
Run 1031351.pdf through CaseStrainer API and save results for comparison.
Extracts text from PDF locally using the same UnifiedTextExtractor as the API,
then submits as text. Ensures test results match file upload and async paths.
"""

import json
import sys
import time
from pathlib import Path

# Add project root for src imports
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import requests

BASE_URL = "http://localhost:5000/casestrainer/api"
ANALYZE_URL = f"{BASE_URL}/analyze"
TASK_STATUS_URL = f"{BASE_URL}/task_status"

PDF_PATH = _project_root / "1031351.pdf"

POLL_INTERVAL = 5
MAX_POLL_WAIT = 600  # 10 min for large doc


def extract_pdf_text(path: Path) -> str:
    """Extract text using UnifiedTextExtractor (same as file upload and RQ worker)."""
    from src.unified_text_extractor import extract_text_from_file_unified

    text, method = extract_text_from_file_unified(str(path), verbose=False)
    return text or ""


def main():
    print(f"Extracting text from {PDF_PATH}...")
    text = extract_pdf_text(PDF_PATH)
    print(f"Extracted {len(text):,} chars")

    print(f"Submitting to {ANALYZE_URL} (type=text)...")
    payload = {"type": "text", "text": text, "force_mode": "async", "enable_verification": True}
    try:
        resp = requests.post(
            ANALYZE_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Submit error: {e}")
        return 1

    task_id = data.get("task_id")
    if not task_id:
        print("No task_id; sync response?")
        result = data
    else:
        print(f"Task: {task_id}, polling (max {MAX_POLL_WAIT}s)...")
        start = time.time()
        while (time.time() - start) < MAX_POLL_WAIT:
            r = requests.get(f"{TASK_STATUS_URL}/{task_id}", timeout=30)
            r.raise_for_status()
            d = r.json()
            status = d.get("status", "").lower()
            if status == "completed":
                result = d
                break
            if status == "failed":
                print(f"Task failed: {d.get('error', 'unknown')}")
                return 1
            time.sleep(POLL_INTERVAL)
        else:
            print("Timeout")
            return 1

    citations = result.get("citations") or result.get("results") or []
    clusters = result.get("clusters") or []
    verified = sum(1 for c in citations if c.get("verified"))

    out_path = Path(__file__).parent.parent / "1031351_actual_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total_citations": len(citations),
                "verified_citations": verified,
                "clusters": len(clusters),
                "citations": citations,
                "clusters_detail": clusters,
            },
            f,
            indent=2,
            default=str,
        )

    print(f"\nResults: {len(citations)} citations, {verified} verified, {len(clusters)} clusters")
    print(f"Saved to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
