#!/usr/bin/env python3
"""
Batch document test for CaseStrainer.
Submits documents (URLs) to the API, collects results, and summarizes.
Start with 3 documents, designed to scale to 20.
"""

import json
import sys
import time
from pathlib import Path

import requests

# API base - adjust if needed
BASE_URL = "http://localhost:5000/casestrainer/api"
ANALYZE_URL = f"{BASE_URL}/analyze"
TASK_STATUS_URL = f"{BASE_URL}/task_status"

# 3 test documents: 2 URLs + 1 text sample (plan to add more up to 20)
# Use CourtListener PDF (known to work) and HTML opinions; Supreme Court PDFs may 404
TEST_DOCS = [
    {
        "type": "url",
        "url": "https://storage.courtlistener.com/pdf/2016/03/01/lockhart_v._united_states.pdf",
        "label": "Lockhart v. United States (SCOTUS 2016)",
    },
    {
        "type": "url",
        "url": "https://www.courtlistener.com/opinion/2773644/united-states-v-ramirez/",
        "label": "United States v. Ramirez (9th Cir.)",
    },
    {
        "type": "text",
        "text": """In Roe v. Wade, 410 U.S. 113 (1973), the Supreme Court held that the Constitution
protects a woman's right to choose. See also Planned Parenthood of Southeastern Pa. v. Casey,
505 U.S. 833 (1992); Lawrence v. Texas, 539 U.S. 558 (2003). The Court in Obergefell v. Hodges,
576 U.S. 644 (2015), extended similar protections. Lower courts have followed these precedents.
E.g., State v. Rohrich, 149 Wash. 2d 647 (2003); Smith v. Jones, 123 F.3d 456 (9th Cir. 1997).""",
        "label": "Sample legal text (mixed citations)",
    },
]

# Additional URLs for scaling to 20 (uncomment as needed)
# SCALE_URLS = [
#     {"url": "https://...", "label": "..."},
# ]

POLL_INTERVAL = 3
MAX_POLL_WAIT = 300  # 5 minutes per document


def submit_document(doc: dict) -> dict:
    """Submit a document (URL or text) to the analyze endpoint. Returns response JSON."""
    if doc.get("type") == "text":
        payload = {"type": "text", "text": doc["text"], "force_mode": "sync", "enable_verification": True}
    else:
        payload = {"type": "url", "url": doc["url"]}
    resp = requests.post(
        ANALYZE_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=90,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"{resp.status_code} {resp.reason}: {resp.text[:500]}")
    return resp.json()


def poll_until_done(task_id: str) -> dict:
    """Poll task_status until completed or failed."""
    start = time.time()
    while (time.time() - start) < MAX_POLL_WAIT:
        resp = requests.get(f"{TASK_STATUS_URL}/{task_id}", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "").lower()
        if status == "completed":
            return data
        if status == "failed":
            raise RuntimeError(data.get("error", "Task failed"))
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"Task {task_id} did not complete within {MAX_POLL_WAIT}s")


def extract_results(response: dict) -> dict:
    """Extract citations, clusters, and stats from analyze or task_status response."""
    # Sync response: results at top level or in result
    citations = response.get("citations") or response.get("results") or []
    clusters = response.get("clusters") or []
    stats = response.get("statistics") or response.get("metadata", {}).get("statistics") or {}
    metadata = response.get("metadata") or {}
    return {
        "citations": citations,
        "clusters": clusters,
        "statistics": stats,
        "metadata": metadata,
    }


def run_single(doc_info: dict) -> dict:
    """Process one document and return results summary."""
    label = doc_info["label"]
    print(f"\n--- {label} ---")
    if doc_info.get("type") == "text":
        print(f"Type: text ({len(doc_info.get('text', ''))} chars)")
    else:
        print(f"URL: {doc_info.get('url', '')[:80]}...")
    try:
        r = submit_document(doc_info)
        task_id = r.get("task_id")
        if task_id:
            print(f"Async task: {task_id}, polling...")
            r = poll_until_done(task_id)
        else:
            print("Sync response received.")
        data = extract_results(r)
        total = len(data["citations"])
        verified = sum(1 for c in data["citations"] if c.get("verified"))
        clusters = len(data["clusters"])
        print(f"Citations: {total} total, {verified} verified; Clusters: {clusters}")
        return {
            "label": label,
            "url": doc_info.get("url", ""),
            "success": True,
            "total_citations": total,
            "verified_citations": verified,
            "clusters": clusters,
            "statistics": data["statistics"],
            "citations_sample": data["citations"][:5],
            "unverified_sample": [c for c in data["citations"] if not c.get("verified")][:5],
        }
    except Exception as e:
        print(f"ERROR: {e}")
        return {
            "label": label,
            "url": doc_info.get("url", ""),
            "type": doc_info.get("type", "url"),
            "success": False,
            "error": str(e),
        }


def main():
    docs = TEST_DOCS[:3]  # Start with 3; increase for full run
    print(f"Testing {len(docs)} documents against {ANALYZE_URL}")
    results = []
    for doc in docs:
        results.append(run_single(doc))
    # Save full results
    out_path = Path(__file__).parent.parent / "batch_test_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    ok = [r for r in results if r.get("success")]
    fail = [r for r in results if not r.get("success")]
    for r in ok:
        print(f"  {r['label']}: {r['total_citations']} citations, {r['verified_citations']} verified")
    for r in fail:
        print(f"  {r['label']}: FAILED - {r.get('error', 'unknown')}")
    print(f"\nPassed: {len(ok)}/{len(results)}")
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
