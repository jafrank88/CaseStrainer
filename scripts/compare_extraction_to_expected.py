#!/usr/bin/env python3
"""
Compare extraction results to expected (golden) fixture.
Lightweight: JSON-only, no PDF extraction. Use separate extraction step to avoid OOM.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def normalize_citation(c: str) -> str:
    """Normalize citation string for comparison."""
    if not c:
        return ""
    s = (c or "").strip().replace("  ", " ")
    s = re.sub(r"\s+", " ", s)
    # Collapse reporter variants: N.Y. -> NY, A.D. -> AD, etc.
    s = re.sub(r"([A-Z])\.([A-Z])\.", r"\1\2", s)
    return s


def normalize_name(name: str) -> str:
    """Normalize case name for comparison."""
    if not name or (name or "").strip().upper() == "N/A":
        return ""
    s = (name or "").strip().rstrip(",").strip()
    return re.sub(r"\s+", " ", s).lower()


def citations_match(a: str, b: str) -> bool:
    """True if citations match (exact or containment)."""
    na, nb = normalize_citation(a), normalize_citation(b)
    if na == nb:
        return True
    if na in nb or nb in na:
        return True
    return False


def extract_citation_set_from_cluster(cluster: Dict[str, Any]) -> Set[str]:
    """Get set of normalized citation strings from a cluster."""
    out = set()
    for c in cluster.get("citations") or cluster.get("citation_objects") or []:
        cit = c.get("citation", "") if isinstance(c, dict) else getattr(c, "citation", "")
        if cit:
            out.add(normalize_citation(cit))
    return out


def extract_citation_set_from_expected(expected: Dict[str, Any]) -> Set[str]:
    """Get set of normalized citation strings from expected cluster."""
    return {normalize_citation(c) for c in expected.get("expected_citations", []) if c}


def get_cluster_name(cluster: Dict[str, Any]) -> str:
    """Get best case name from cluster."""
    name = cluster.get("extracted_case_name") or cluster.get("case_name") or cluster.get("verifying_display_name") or ""
    if name:
        return name
    for c in cluster.get("citations") or cluster.get("citation_objects") or []:
        if isinstance(c, dict):
            n = c.get("extracted_case_name") or c.get("canonical_name")
            if n:
                return n
    return ""


def get_cluster_year(cluster: Dict[str, Any]) -> str:
    """Get best year from cluster."""
    y = cluster.get("extracted_date") or cluster.get("date") or cluster.get("verifying_display_date")
    if y:
        return str(y).strip()
    for c in cluster.get("citations") or cluster.get("citation_objects") or []:
        if isinstance(c, dict):
            y = c.get("extracted_date") or c.get("canonical_date")
            if y:
                return str(y).strip()
    return ""


def _count_containment_overlap(exp_cits: Set[str], act_cits: Set[str]) -> int:
    """Count how many expected citations are found in actual (exact or containment)."""
    count = 0
    for en in exp_cits:
        if en in act_cits:
            count += 1
            continue
        for a in act_cits:
            if en in a or a in en:
                count += 1
                break
    return count


def find_matching_actual_cluster(
    expected: Dict[str, Any],
    actual_clusters: List[Dict[str, Any]],
    used: Set[int],
) -> Optional[Tuple[int, Dict[str, Any]]]:
    """Find actual cluster that best matches expected by citation overlap."""
    exp_cits = extract_citation_set_from_expected(expected)
    if not exp_cits:
        return None

    best_idx = None
    best_overlap = 0

    for i, ac in enumerate(actual_clusters):
        if i in used:
            continue
        act_cits = extract_citation_set_from_cluster(ac)
        overlap = _count_containment_overlap(exp_cits, act_cits)
        if overlap > best_overlap:
            best_overlap = overlap
            best_idx = i

    if best_idx is not None and best_overlap > 0:
        return (best_idx, actual_clusters[best_idx])
    return None


def compare_one(
    expected: Dict[str, Any],
    actual: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compare one expected cluster to actual (or None if no match)."""
    exp_name = (expected.get("expected_case_name") or "").strip()
    exp_year = (expected.get("expected_year") or "").strip()
    exp_cits = expected.get("expected_citations", [])

    result = {
        "expected_case_name": exp_name,
        "expected_year": exp_year,
        "expected_citations": exp_cits,
        "matched": actual is not None,
        "actual_case_name": "",
        "actual_year": "",
        "actual_citations": [],
        "name_match": False,
        "year_match": False,
        "citation_missing": [],
        "citation_extra": [],
    }

    if not actual:
        result["citation_missing"] = exp_cits
        return result

    act_name = get_cluster_name(actual)
    act_year = get_cluster_year(actual)
    act_cits = extract_citation_set_from_cluster(actual)

    result["actual_case_name"] = act_name
    result["actual_year"] = act_year
    result["actual_citations"] = list(act_cits)

    # Exact match, or prefix match (e.g. "Dow v. Caribou" matches "Dow v. Caribou Chamber of Commerce")
    exp_norm = normalize_name(exp_name)
    act_norm = normalize_name(act_name)
    result["name_match"] = bool(
        act_name and exp_name
        and (exp_norm == act_norm or act_norm.startswith(exp_norm + " ") or exp_norm.startswith(act_norm + " "))
    )

    result["year_match"] = exp_year == act_year or (not exp_year and not act_year)

    def _citation_found(exp_cit: str, actual_set: Set[str]) -> bool:
        """True if expected citation is in actual (exact or containment)."""
        en = normalize_citation(exp_cit)
        if en in actual_set:
            return True
        for a in actual_set:
            if en in a or a in en:
                return True
        return False

    def _actual_matches_expected(act: str, exp_cits: List[str]) -> bool:
        """True if actual citation matches any expected (exact or containment)."""
        for e in exp_cits:
            en = normalize_citation(e)
            if en == act or en in act or act in en:
                return True
        return False

    result["citation_missing"] = [c for c in exp_cits if not _citation_found(c, act_cits)]
    result["citation_extra"] = [a for a in act_cits if not _actual_matches_expected(a, exp_cits)]

    return result


def run_comparison(expected_path: Path, actual_path: Path) -> Dict[str, Any]:
    """Load both JSONs and compare. Returns comparison result dict."""
    with open(expected_path, encoding="utf-8") as f:
        expected_data = json.load(f)

    with open(actual_path, encoding="utf-8") as f:
        actual_data = json.load(f)

    expected_clusters = expected_data.get("expected_clusters", [])
    actual_clusters = actual_data.get("clusters", [])

    if not actual_clusters and "citations" in actual_data:
        citations = actual_data.get("citations", [])
        if citations:
            actual_clusters = [{"citations": citations}]

    used = set()
    comparisons = []

    for exp in expected_clusters:
        match = find_matching_actual_cluster(exp, actual_clusters, used)
        if match:
            idx, act = match
            used.add(idx)
        else:
            act = None
        comparisons.append(compare_one(exp, act))

    matched = sum(1 for c in comparisons if c["matched"])
    name_ok = sum(1 for c in comparisons if c["name_match"])
    year_ok = sum(1 for c in comparisons if c["year_match"])
    total_exp_cits = sum(len(e.get("expected_citations", [])) for e in expected_clusters)
    found_cits = total_exp_cits - sum(len(c["citation_missing"]) for c in comparisons)

    return {
        "document_id": expected_data.get("document_id", "?"),
        "expected_clusters": len(expected_clusters),
        "actual_clusters": len(actual_clusters),
        "comparisons": comparisons,
        "summary": {
            "matched_clusters": matched,
            "name_accuracy": name_ok,
            "year_accuracy": year_ok,
            "citation_recall": found_cits,
            "citation_total_expected": total_exp_cits,
        },
    }


def print_report(result: Dict[str, Any]) -> None:
    """Print human-readable comparison report."""
    s = result.get("summary", {})
    comps = result.get("comparisons", [])

    print("=" * 70)
    print(f"EXTRACTION COMPARISON: {result.get('document_id', '?')}")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  Expected clusters:    {result.get('expected_clusters', 0)}")
    print(f"  Actual clusters:      {result.get('actual_clusters', 0)}")
    print(f"  Matched clusters:     {s.get('matched_clusters', 0)}")
    print(f"  Name accuracy:       {s.get('name_accuracy', 0)}/{len(comps)}")
    print(f"  Year accuracy:       {s.get('year_accuracy', 0)}/{len(comps)}")
    print(f"  Citation recall:     {s.get('citation_recall', 0)}/{s.get('citation_total_expected', 0)}")
    print()

    for i, c in enumerate(comps, 1):
        status = "OK" if c["matched"] else "MISSING"
        name_ok = "OK" if c["name_match"] else "DIFF"
        year_ok = "OK" if c["year_match"] else "DIFF"
        print(f"[{i}] {c['expected_case_name']} ({status})")
        print(f"    Name: {name_ok}  |  Year: {year_ok}")
        if c["actual_case_name"] and not c["name_match"]:
            print(f"    Expected name: {c['expected_case_name']}")
            print(f"    Actual name:   {c['actual_case_name']}")
        if c["expected_year"] and c["actual_year"] and not c["year_match"]:
            print(f"    Expected year: {c['expected_year']}  |  Actual: {c['actual_year']}")
        if c["citation_missing"]:
            print(f"    Missing citations: {c['citation_missing']}")
        print()

    print("VERDICT:")
    if s.get("matched_clusters") == len(comps) and all(x["name_match"] and x["year_match"] for x in comps):
        print("  PASS: All expected clusters matched with correct name and year.")
    elif s.get("matched_clusters") == len(comps):
        print("  PARTIAL: All clusters matched but some name/year differences.")
    else:
        print(f"  FAIL: {len(comps) - s.get('matched_clusters', 0)} expected cluster(s) not found.")


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python compare_extraction_to_expected.py <expected.json> <actual.json>")
        return 1

    expected_path = Path(sys.argv[1])
    actual_path = Path(sys.argv[2])

    if not expected_path.exists():
        print(f"Error: Expected file not found: {expected_path}")
        return 1
    if not actual_path.exists():
        print(f"Error: Actual file not found: {actual_path}")
        return 1

    result = run_comparison(expected_path, actual_path)
    print_report(result)

    out_path = actual_path.parent / f"{actual_path.stem}_comparison.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nDetailed result saved to: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
