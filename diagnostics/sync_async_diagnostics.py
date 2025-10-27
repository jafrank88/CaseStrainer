#!/usr/bin/env python3
"""
Sync vs Async Verification Diagnostics

- Submits the same text to /casestrainer/api/analyze in two modes:
  1) Sync/immediate (short text)
  2) Forced-async (same text padded >5KB)
- Polls task status if queued/processing
- Compares verification outcomes and prints a concise diff

Override BASE_URL with env var if needed (default: https://localhost/casestrainer/api)
"""
import os
import time
import json
import sys
import argparse
from typing import Dict, Any, Tuple

import requests
requests.packages.urllib3.disable_warnings()  # allow self-signed in dev

def _resolve_base_url() -> str:
    """Resolve BASE_URL from CLI arg, then env, then default."""
    parser = argparse.ArgumentParser(description="Sync vs Async Verification Diagnostics")
    parser.add_argument("--base-url", dest="base_url", default=None, help="Base API URL, e.g. https://wolf.law.uw.edu/casestrainer/api")
    # Parse only known args so this can be imported without failing
    args, _ = parser.parse_known_args()
    if args.base_url:
        return args.base_url.strip()
    env = os.environ.get("BASE_URL")
    if env:
        return env.strip()
    return "https://localhost/casestrainer/api"

BASE_URL = _resolve_base_url()
ANALYZE_URL = f"{BASE_URL}/analyze"
TASK_URL = f"{BASE_URL}/task_status/{{task_id}}"

DEFAULT_TEXT = """
Fischer v. Kenai Peninsula Borough Sch. Dist. (2024)
548 P.3d 1086 (2024)

Fed'n of Pa., Inc. v. Commonwealth (2009)
970 A.2d 1108 (2009)

Elite Indus., Inc. v. Pa. Pub. Util. Comm'n (1968)
390 U.S. 747 (1968)

Interior Alaska Airboat Ass'n, Inc. v. State, Bd. of Game (2024)
758 F.3d 1179 (2024)
""".strip()


def _post_analyze(text: str, timeout: int = 90) -> Dict[str, Any]:
    """POST to /analyze and return final result, polling if queued/processing."""
    payload = {"type": "text", "text": text}
    r = requests.post(ANALYZE_URL, json=payload, timeout=timeout, verify=False)
    r.raise_for_status()
    data = r.json()

    status = data.get("status") or data.get("result", {}).get("status")
    task_id = data.get("task_id") or data.get("result", {}).get("task_id")

    # If queued/processing, poll task status
    if status in {"queued", "processing"} and task_id:
        for i in range(120):  # up to 120 seconds
            time.sleep(1)
            sr = requests.get(TASK_URL.format(task_id=task_id), timeout=30, verify=False)
            if sr.status_code != 200:
                continue
            sd = sr.json()
            if sd.get("status") == "completed":
                return sd.get("result") or sd
            if sd.get("status") == "failed":
                raise RuntimeError(f"Async task failed: {sd.get('error')}")
        raise TimeoutError("Timed out waiting for async task to complete")

    return data


def _extract_results(resp: Dict[str, Any]) -> Tuple[list, list]:
    """Return (citations, clusters) lists from either flat or nested response."""
    # Prefer nested 'result' shape if present
    res = resp.get("result") if isinstance(resp, dict) else None
    if isinstance(res, dict):
        return res.get("citations", []) or [], res.get("clusters", []) or []
    # Fallback to flat keys
    return resp.get("citations", []) or [], resp.get("clusters", []) or []


def _index_citations(citations: list) -> Dict[str, Dict[str, Any]]:
    idx = {}
    for c in citations:
        if isinstance(c, dict):
            key = c.get("citation")
            if key:
                idx[key] = {
                    "verified": bool(c.get("verified", False)),
                    "canonical_name": c.get("canonical_name"),
                    "canonical_date": c.get("canonical_date"),
                    "canonical_url": c.get("canonical_url"),
                    "extracted_case_name": c.get("extracted_case_name"),
                    "extracted_date": c.get("extracted_date"),
                    "error": c.get("error") or c.get("verification_error"),
                    "source": c.get("verification_source") or c.get("source"),
                }
    return idx


def main() -> int:
    # Parse optional text inputs
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--text", dest="text", default=None)
    parser.add_argument("--text-file", dest="text_file", default=None)
    args, _ = parser.parse_known_args()

    if args.text_file and os.path.exists(args.text_file):
        with open(args.text_file, 'r', encoding='utf-8') as f:
            input_text = f.read()
    else:
        input_text = args.text or DEFAULT_TEXT

    print(f"BASE_URL: {BASE_URL}")
    print("Submitting SYNC (short) request...")
    t0 = time.time()
    sync_resp = _post_analyze(input_text)
    t1 = time.time()

    print("Submitting ASYNC (forced with padding) request...")
    padding = "\n" + ("Lorem ipsum dolor sit amet. " * 300)
    async_resp = _post_analyze(input_text + padding)
    t2 = time.time()

    sync_cits, sync_clusters = _extract_results(sync_resp)
    async_cits, async_clusters = _extract_results(async_resp)

    sync_idx = _index_citations(sync_cits)
    async_idx = _index_citations(async_cits)

    # Summary
    print("\n=== SUMMARY ===")
    print(f"Sync:  {len(sync_cits)} citations, {len(sync_clusters)} clusters in {t1 - t0:.2f}s")
    print(f"Async: {len(async_cits)} citations, {len(async_clusters)} clusters in {t2 - t1:.2f}s")

    # Differences
    print("\n=== VERIFICATION DIFF (sync vs async) ===")
    all_keys = sorted(set(sync_idx.keys()) | set(async_idx.keys()))
    diff_count = 0
    for k in all_keys:
        s = sync_idx.get(k)
        a = async_idx.get(k)
        s_v = s and s.get("verified")
        a_v = a and a.get("verified")
        if s_v != a_v:
            diff_count += 1
            print(f"- {k}: sync={'✅' if s_v else '❌'} vs async={'✅' if a_v else '❌'}")
            if s and a:
                print(f"    sync src={s.get('source')} url={s.get('canonical_url')} err={s.get('error')}")
                print(f"    async src={a.get('source')} url={a.get('canonical_url')} err={a.get('error')}")
    if diff_count == 0:
        print("(no verification status differences)")

    # List unverified with reasons (if any)
    def _unv(idx: Dict[str, Dict[str, Any]]):
        return {k: v for k, v in idx.items() if not v.get('verified')}

    print("\n=== UNVERIFIED (SYNC) ===")
    for k, v in _unv(sync_idx).items():
        print(f"- {k}: err={v.get('error')} src={v.get('source')}")

    print("\n=== UNVERIFIED (ASYNC) ===")
    for k, v in _unv(async_idx).items():
        print(f"- {k}: err={v.get('error')} src={v.get('source')}")

    # Exit code for CI
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(2)
