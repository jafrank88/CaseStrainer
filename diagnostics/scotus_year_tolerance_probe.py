#!/usr/bin/env python3
"""
Probe year-alignment behavior for CourtListener results.

This script has two modes:
1) Live API probe: sends sample text to /analyze and prints year-source metadata.
2) Policy probe: directly exercises UnifiedCitationProcessorV2 year alignment with
   crafted CourtListener year offsets to verify the SCOTUS-only -1 rule.

Usage:
  python diagnostics/scotus_year_tolerance_probe.py --base-url http://localhost:5000/casestrainer/api
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List

import requests


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _extract_citations(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    top = payload.get("citations")
    if isinstance(top, list):
        return top
    nested = payload.get("result")
    if isinstance(nested, dict) and isinstance(nested.get("citations"), list):
        return nested.get("citations") or []
    return []


def run_live_probe(base_url: str, timeout: int) -> int:
    url = f"{base_url.rstrip('/')}/analyze"
    samples = [
        ("scotus", "Spokeo, Inc. v. Robins, 2016, 578 U.S. 330."),
        ("non_scotus", "Rio Grande Community Health Center, Inc. v. Rullan, 2005, 397 F.3d 56."),
    ]

    print(f"[LIVE] Endpoint: {url}")
    failures = 0

    for label, text in samples:
        payload = {"type": "text", "text": text, "force_mode": "sync"}
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            print(f"\n[{label}] status={resp.status_code}")
            if resp.status_code != 200:
                print(resp.text[:800])
                failures += 1
                continue

            data = resp.json() if "json" in (resp.headers.get("content-type", "").lower()) else {}
            cits = _extract_citations(data)
            print(f"[{label}] citations={len(cits)}")
            for c in cits[:5]:
                md = c.get("metadata") if isinstance(c.get("metadata"), dict) else {}
                print(
                    json.dumps(
                        {
                            "citation": c.get("citation"),
                            "source": c.get("source"),
                            "verified": c.get("verified"),
                            "canonical_date": c.get("canonical_date"),
                            "extracted_date": c.get("extracted_date"),
                            "year_source": md.get("year_source"),
                            "year_compare_value": md.get("year_compare_value"),
                            "year_mismatch_type": md.get("year_mismatch_type"),
                        },
                        ensure_ascii=True,
                    )
                )
        except Exception as err:
            print(f"[{label}] ERROR: {err}")
            failures += 1

    return failures


def run_policy_probe() -> int:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

    proc = UnifiedCitationProcessorV2.__new__(UnifiedCitationProcessorV2)
    checks = [
        {
            "name": "scotus_minus_one_allowed",
            "citation": "578 U.S. 330",
            "extracted": "2016",
            "canonical": "2015-12-31",
            "source": "CourtListener",
            "expect_accept": True,
            "expect_compare_source": "scotus_cl_minus_one",
        },
        {
            "name": "non_scotus_minus_one_rejected",
            "citation": "397 F.3d 56",
            "extracted": "2005",
            "canonical": "2004-12-01",
            "source": "CourtListener",
            "expect_accept": False,
            "expect_compare_source": "canonical_date",
        },
    ]

    print("\n[POLICY] Local year-alignment checks")
    failures = 0
    for c in checks:
        res = proc._evaluate_year_alignment(
            citation_text=c["citation"],
            extracted_date=c["extracted"],
            canonical_date=c["canonical"],
            verification_source=c["source"],
            in_toa_section=False,
            allow_soft_mismatch=False,
        )
        ok = bool(
            res.get("accept") is c["expect_accept"]
            and str(res.get("compare_source")) == str(c["expect_compare_source"])
        )
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {c['name']} -> {res}")
        if not ok:
            failures += 1
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default="http://localhost:5000/casestrainer/api",
        help="Base API URL without trailing /analyze",
    )
    parser.add_argument("--timeout", type=int, default=120, help="HTTP timeout in seconds")
    parser.add_argument(
        "--policy-only",
        action="store_true",
        help="Skip live API calls and only run local policy checks",
    )
    args = parser.parse_args()

    failures = 0
    if not args.policy_only:
        failures += run_live_probe(args.base_url, args.timeout)
    failures += run_policy_probe()

    print(f"\nDone. failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
