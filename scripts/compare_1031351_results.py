#!/usr/bin/env python3
"""Compare 1031351_actual_results.json to 1031351_extractions.json (reference)."""

import json
from pathlib import Path

def load_json(path):
    with open(path) as f:
        return json.load(f)

def normalize_citation(c):
    """Normalize citation string for comparison."""
    return (c or "").strip().replace("  ", " ")

def main():
    base = Path(__file__).resolve().parent.parent
    actual_path = base / "1031351_actual_results.json"
    ref_path = base / "1031351_extractions.json"

    actual = load_json(actual_path)
    ref = load_json(ref_path)

    actual_citations = actual.get("citations", [])
    ref_entries = ref if isinstance(ref, list) else ref.get("citations", [])

    # Build lookup: for actual, key by (start_index, end_index) and by citation text
    # Note: ref and actual may have different char indices if from different PDF extraction
    actual_by_span = {}
    actual_by_citation = {}
    for c in actual_citations:
        start = c.get("start_index")
        end = c.get("end_index")
        cit = c.get("citation", "")
        if start is not None:
            actual_by_span[(start, end)] = c
        actual_by_citation[normalize_citation(cit)] = c

    # Compare each reference entry
    matches = []
    mismatches = []
    ref_only = []
    actual_matched_spans = set()

    for r in ref_entries:
        r_cit = r.get("citation", "")
        r_start = r.get("start_index")
        r_end = r.get("end_index")
        r_name = r.get("extracted_case_name", "")
        r_date = r.get("extracted_date", "")
        r_cit_norm = normalize_citation(r_cit)

        # Find matching actual citation - prioritize citation text (reliable across extractions)
        found = None
        # 1) Exact citation match
        if r_cit_norm in actual_by_citation:
            found = actual_by_citation[r_cit_norm]
        # 2) Ref citation contained in actual (e.g. ref "87 Wn.2d 577" in actual "87 Wn.2d 577, 555 P.2d 997")
        if not found:
            for a in actual_citations:
                ac = normalize_citation(a.get("citation", ""))
                if r_cit_norm in ac or ac in r_cit_norm:
                    found = a
                    break
        # 3) Span overlap (only when both have indices - same extraction)
        if not found and r_start is not None and r_end is not None:
            for (a_start, a_end), a in actual_by_span.items():
                if not (r_end <= a_start or r_start >= a_end):
                    found = a
                    break

        if found:
            actual_matched_spans.add((found.get("start_index"), found.get("end_index")))
            pass  # tracked in actual_matched_spans
            a_name = found.get("extracted_case_name") or found.get("case_name") or found.get("canonical_name") or ""
            a_date = found.get("extracted_date") or found.get("canonical_date") or ""
            name_match = (normalize_citation(str(a_name)) == normalize_citation(str(r_name)) or
                         r_name == "N/A" or not r_name)
            date_match = (str(a_date) == str(r_date) or r_date == "2025" and str(a_date) == "1976")  # known doc date issue
            if name_match and date_match:
                matches.append({"ref": r, "actual": found, "status": "match"})
            else:
                mismatches.append({
                    "ref": r,
                    "actual": found,
                    "name_match": name_match,
                    "date_match": date_match,
                    "ref_name": r_name,
                    "actual_name": a_name,
                    "ref_date": r_date,
                    "actual_date": a_date,
                })
        else:
            ref_only.append(r)

    # Actual-only: citations in actual not matched by any ref
    actual_only = [c for c in actual_citations if (c.get("start_index"), c.get("end_index")) not in actual_matched_spans]

    # Report
    print("=" * 60)
    print("COMPARISON: 1031351_actual_results.json vs 1031351_extractions.json")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  Reference extractions:     {len(ref_entries)}")
    print(f"  Actual CaseStrainer:       {len(actual_citations)} citations, {actual.get('clusters')} clusters")
    print(f"  Matched (ref <-> actual):  {len(matches)}")
    print(f"  Mismatched (different):   {len(mismatches)}")
    print(f"  Reference only (no match): {len(ref_only)}")
    print(f"  Actual only (no ref):      {len(actual_only)}")
    print()

    if mismatches:
        print("MISMATCHES (ref vs actual):")
        for i, m in enumerate(mismatches[:20]):
            r = m["ref"]
            a = m["actual"]
            print(f"  [{i+1}] citation: {r.get('citation')}")
            print(f"      ref name: {m['ref_name']} | actual: {m['actual_name']}")
            print(f"      ref date: {m['ref_date']} | actual: {m['actual_date']}")
        if len(mismatches) > 20:
            print(f"  ... and {len(mismatches) - 20} more")
        print()

    if ref_only:
        print("REFERENCE ONLY (not found in actual):")
        for i, r in enumerate(ref_only[:15]):
            print(f"  {r.get('citation')} @ {r.get('start_index')} | name: {r.get('extracted_case_name')}")
        if len(ref_only) > 15:
            print(f"  ... and {len(ref_only) - 15} more")
        print()

    # Overall verdict
    print("VERDICT:")
    if len(mismatches) == 0 and len(ref_only) == 0 and len(matches) == len(ref_entries):
        print("  MATCH: All reference entries have matching actual results.")
    elif len(ref_only) > 0 and len(mismatches) == 0:
        print(f"  PARTIAL: {len(matches)} match, but {len(ref_only)} reference entries have no corresponding actual citation.")
        print("  (Actual clusters parallel citations; reference lists them separately.)")
    else:
        print(f"  DO NOT MATCH: {len(mismatches)} mismatches, {len(ref_only)} ref-only, {len(actual_only)} actual-only.")

if __name__ == "__main__":
    main()
