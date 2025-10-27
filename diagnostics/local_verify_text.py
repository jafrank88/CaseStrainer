#!/usr/bin/env python3
"""
Run local extraction + clustering + verification on provided text
and print concise results.

Usage:
  python diagnostics/local_verify_text.py --text "..."
  or provide no args to use the built-in four-citation sample.
"""
import os
import sys
import json
import argparse

# Ensure project root is on sys.path so `src` package is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.citation_extraction_endpoint import extract_citations_with_clustering

DEFAULT_TEXT = (
    "Fischer v. Kenai Peninsula Borough Sch. Dist. (2024)\n"
    "548 P.3d 1086 (2024)\n\n"
    "Fed'n of Pa., Inc. v. Commonwealth (2009)\n"
    "970 A.2d 1108 (2009)\n\n"
    "Elite Indus., Inc. v. Pa. Pub. Util. Comm'n (1968)\n"
    "390 U.S. 747 (1968)\n\n"
    "Interior Alaska Airboat Ass'n, Inc. v. State, Bd. of Game (2024)\n"
    "758 F.3d 1179 (2024)\n"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", dest="text", default=None, help="Text to analyze")
    args = ap.parse_args()

    text = args.text or DEFAULT_TEXT

    result = extract_citations_with_clustering(text, enable_verification=True)
    citations = result.get('citations', [])

    print("=== LOCAL PIPELINE RESULT ===")
    print(f"Citations: {len(citations)}  Clusters: {len(result.get('clusters', []))}")

    for c in citations:
        cit = c.get('citation')
        verified = c.get('verified', False)
        source = c.get('verification_source') or c.get('source')
        err = c.get('verification_error') or c.get('error')
        cname = c.get('canonical_name')
        cdate = c.get('canonical_date')
        curl = c.get('canonical_url')
        print(f"- {cit}: {'✅' if verified else '❌'} src={source} name={cname} date={cdate} url={curl} err={err}")

    # Print JSON if desired
    # print(json.dumps(result, indent=2, default=str))

if __name__ == '__main__':
    sys.exit(main())
