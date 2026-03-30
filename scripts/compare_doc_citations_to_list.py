#!/usr/bin/env python3
"""
Extract citations from a PDF using CaseStrainer pipeline, then list those
that are NOT in a provided CaseStrainer result list.
Usage: python scripts/compare_doc_citations_to_list.py <path_to_pdf>
"""
import asyncio
import re
import sys
from pathlib import Path

# CaseStrainer list: all citation strings from the user's 70 cases / 108 citations.
# (Citation 1: / Citation 2: lines from the UI output.)
CITATIONS_IN_LIST = """
10 Tenn. 581
521 U.S. 811
504 U.S. 555
578 U.S. 330
497 U.S. 1
491 U.S. 440
926 F.3d 329
1 Cranch 137
555 U.S. 488
468 U.S. 737
964 F.3d 990
528 U.S. 167
422 U.S. 490
410 U.S. 614
568 U.S. 398
951 F.3d 1008
554 U.S. 724
462 U.S. 919
588 U.S. ___
573 U.S. 149
481 U.S. 465
950 F.3d 458
555 U.S. 460
882 F.3d 616
496 U.S. 310
219 U.S. 346
577 U.S. 442
942 F.3d 1259
418 U.S. 323
879 F.3d 339
836 F.3d 925
846 F.3d 909
150 Va. 301
143 S.E. 631
639 F. App'x 582
256 N.Y. 36
175 N.E. 505
461 U.S. 95
495 U.S. 149
306 U.S. 208
617 F.3d 688
424 U.S. 800
590 U.S. ___
29 F. Cas. 1120
10 How. 477
533 U.S. 606
258 U.S. 126
996 F.3d 1110
397 U.S. 150
4 Wheat. 316
923 F.3d 458
958 F.3d, 617
958 F.3d 617
29 F. Cas. 506
96 Wis. 386
71 N.W. 596
183 N.C. 309
111 S.E. 517
74 N.D. 525
259 Va. 568
528 S.E.2d 119
593 U.S. ___
200 U.S. 321
2016 WL 6070490
418 U.S. 208
387 U.S. 136
979 F.3d 917
584 U.S. ___
592 U.S. ___
426 U.S. 26
524 U.S. 11
554 U.S. 269
523 U.S. 83
6 Wheat. 264
455 U.S. 363
490 U.S. 605
199 F.3d 263
""".strip().splitlines()


def normalize(s: str) -> str:
    """Strip and collapse spaces for comparison."""
    if not s:
        return ""
    return " ".join(s.split()).strip()


def build_list_set():
    """Build set of normalized citation strings from the CaseStrainer list."""
    out = set()
    for line in CITATIONS_IN_LIST:
        line = line.strip()
        if not line:
            continue
        # Remove trailing "Verified" / "Unverified" if present
        for suffix in ("Verified", "Unverified"):
            if line.endswith(suffix):
                line = line[: -len(suffix)].strip()
        n = normalize(line)
        if n:
            out.add(n)
        # Also add variant without comma before page (e.g. "958 F.3d 617")
        if "," in n:
            out.add(normalize(n.replace(",", " ")))
    return out


def extract_citation_strings_from_result(result: dict) -> set:
    """Collect all citation strings from pipeline result (clusters + parallel)."""
    out = set()
    clusters = result.get("clusters") or []
    for cluster in clusters:
        for cit in cluster.get("citations") or []:
            if isinstance(cit, dict):
                c = cit.get("citation") or ""
                if c:
                    out.add(normalize(c))
                for p in cit.get("parallel_citations") or []:
                    if p:
                        out.add(normalize(str(p)))
    # Also from flat citations if present
    for cit in result.get("citations") or []:
        if isinstance(cit, dict):
            c = cit.get("citation") or ""
            if c:
                out.add(normalize(c))
            for p in cit.get("parallel_citations") or []:
                if p:
                    out.add(normalize(str(p)))
    return out


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/compare_doc_citations_to_list.py <path_to_pdf>")
        sys.exit(1)
    pdf_path = Path(sys.argv[1]).resolve()
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    # Ensure we can import from project root
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from src.robust_pdf_extractor import extract_text_from_pdf_smart
    from src.unified_processing_pipeline import process_citations_unified

    print("Extracting text from PDF...")
    text = extract_text_from_pdf_smart(str(pdf_path))
    if not text or len(text.strip()) < 100:
        print("PDF produced little or no text. It may be scanned/image-only or empty.")
        sys.exit(1)
    print(f"Extracted {len(text)} characters.")

    print("Running citation extraction (no verification)...")
    result = asyncio.run(
        process_citations_unified(
            text,
            processing_mode="enhanced_sync",
            enable_verification=False,
            enable_parallel_verification=False,
        )
    )

    doc_citations = extract_citation_strings_from_result(result)
    list_set = build_list_set()

    not_in_list = sorted(doc_citations - list_set)
    in_list = sorted(doc_citations & list_set)

    print()
    print("=== Citations IN the document but NOT in your CaseStrainer list ===")
    if not_in_list:
        for c in not_in_list:
            print(c)
        print(f"\nTotal: {len(not_in_list)} citation(s) in document not in list.")
    else:
        print("(None - every citation found in the document appears in your list.)")
    print()
    print(f"Citations in document that ARE in list: {len(in_list)}")
    print(f"Total unique citation strings from document: {len(doc_citations)}")


if __name__ == "__main__":
    main()
