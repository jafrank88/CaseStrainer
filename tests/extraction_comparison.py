"""
Compare ideal (golden) extraction results with actual tool output.

Usage:
  from tests.extraction_comparison import compare_expected_vs_actual, load_expected_fixture

  expected = load_expected_fixture("1033397_expected.json")
  report = compare_expected_vs_actual(expected, actual_result)
  print_extraction_report(report)
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def normalize_citation(c: str) -> str:
    """Normalize citation string for comparison."""
    if not c:
        return ""
    s = (c or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _citation_matches(a: str, b: str) -> bool:
    """True if citations match (exact or containment)."""
    na, nb = normalize_citation(a), normalize_citation(b)
    if na == nb:
        return True
    if na in nb or nb in na:
        return True
    return False


def _find_citation_in_list(cit: str, items: List[Dict]) -> Optional[Dict]:
    """Find a citation in a list of citation dicts (by citation key)."""
    n = normalize_citation(cit)
    for item in items:
        c = item.get("citation", "")
        if _citation_matches(cit, c):
            return item
    return None


def _get_cluster_citations(cluster: Dict) -> List[str]:
    """Extract citation strings from a cluster (citations or citation_objects)."""
    out = []
    for c in cluster.get("citations", []) or cluster.get("citation_objects", []):
        if isinstance(c, dict):
            cit = c.get("citation", "")
        else:
            cit = getattr(c, "citation", None) or str(c)
        if cit:
            out.append(cit)
    return out


def _get_cluster_name(cluster: Dict) -> str:
    """Best case name from cluster."""
    return (
        cluster.get("extracted_case_name")
        or cluster.get("canonical_name")
        or cluster.get("case_name")
        or cluster.get("verifying_display_name")
        or ""
    )


def _get_cluster_year(cluster: Dict) -> str:
    """Best year from cluster."""
    return str(
        cluster.get("extracted_date")
        or cluster.get("canonical_date")
        or cluster.get("date")
        or cluster.get("verifying_display_date")
        or ""
    )


def _normalize_name(name: str) -> str:
    """Normalize case name for comparison."""
    if not name:
        return ""
    s = name.strip().rstrip(",")
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def _name_matches(expected: str, actual: str) -> bool:
    """Check if names match (normalized, allow expected to be substring of actual)."""
    ne, na = _normalize_name(expected), _normalize_name(actual)
    if not ne:
        return True
    if ne == na:
        return True
    if ne in na or na in ne:
        return True
    return False


def load_expected_fixture(name: str) -> Dict[str, Any]:
    """Load expected fixture from tests/fixtures/."""
    path = FIXTURES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Fixture not found: {path}")
    import json

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compare_expected_vs_actual(
    expected: Dict[str, Any],
    actual: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compare expected clusters with actual API/processor output.

    expected: { "expected_clusters": [ { expected_case_name, expected_citations, expected_year } ] }
    actual:   { "clusters": [ { citations: [...], extracted_case_name, extracted_date, ... } ] }

    Returns a report dict with matches, mismatches, and metrics.
    """
    expected_clusters = expected.get("expected_clusters", [])
    actual_clusters = actual.get("clusters", [])

    report = {
        "document_id": expected.get("document_id", "unknown"),
        "expected_cluster_count": len(expected_clusters),
        "actual_cluster_count": len(actual_clusters),
        "matches": [],
        "mismatches": [],
        "expected_only": [],
        "actual_only": [],
        "metrics": {
            "cluster_match_count": 0,
            "citation_recall": 0,
            "citation_expected_total": 0,
            "name_accuracy": 0,
            "year_accuracy": 0,
        },
    }

    # Build set of expected citation strings (for recall)
    all_expected_cits = set()
    for ec in expected_clusters:
        for c in ec.get("expected_citations", []):
            all_expected_cits.add(normalize_citation(c))
    report["metrics"]["citation_expected_total"] = len(all_expected_cits)

    # Build actual citation -> cluster lookup
    actual_cit_to_cluster: Dict[str, Dict] = {}
    for ac in actual_clusters:
        for cit in _get_cluster_citations(ac):
            actual_cit_to_cluster[normalize_citation(cit)] = ac

    matched_actual_indices = set()

    for i, exp_cluster in enumerate(expected_clusters):
        exp_name = exp_cluster.get("expected_case_name", "")
        exp_cits = exp_cluster.get("expected_citations", [])
        exp_year = str(exp_cluster.get("expected_year", ""))

        # Find best-matching actual cluster by citation overlap
        best_actual: Optional[Dict] = None
        best_overlap = 0
        best_idx = -1

        for j, act_cluster in enumerate(actual_clusters):
            act_cits = _get_cluster_citations(act_cluster)
            overlap = 0
            for ec in exp_cits:
                nec = normalize_citation(ec)
                for ac in act_cits:
                    if _citation_matches(ec, ac):
                        overlap += 1
                        break
            if overlap > best_overlap:
                best_overlap = overlap
                best_actual = act_cluster
                best_idx = j

        if best_actual is None or best_overlap == 0:
            report["expected_only"].append(
                {"expected_case_name": exp_name, "expected_citations": exp_cits, "expected_year": exp_year}
            )
            continue

        matched_actual_indices.add(best_idx)
        act_name = _get_cluster_name(best_actual)
        act_year = _get_cluster_year(best_actual)

        # Citation recall for this cluster
        found_cits = []
        missing_cits = []
        for ec in exp_cits:
            if any(_citation_matches(ec, ac) for ac in _get_cluster_citations(best_actual)):
                found_cits.append(ec)
            else:
                missing_cits.append(ec)

        name_ok = _name_matches(exp_name, act_name)
        year_ok = (exp_year == act_year) or (not exp_year and not act_year)

        if name_ok and year_ok and not missing_cits:
            report["matches"].append(
                {
                    "expected_case_name": exp_name,
                    "actual_case_name": act_name,
                    "expected_year": exp_year,
                    "actual_year": act_year,
                    "expected_citations": exp_cits,
                    "found_citations": found_cits,
                }
            )
            report["metrics"]["cluster_match_count"] += 1
            report["metrics"]["name_accuracy"] += 1
            report["metrics"]["year_accuracy"] += 1
            report["metrics"]["citation_recall"] += len(found_cits)
        else:
            report["mismatches"].append(
                {
                    "expected_case_name": exp_name,
                    "actual_case_name": act_name,
                    "expected_year": exp_year,
                    "actual_year": act_year,
                    "expected_citations": exp_cits,
                    "found_citations": found_cits,
                    "missing_citations": missing_cits,
                    "name_match": name_ok,
                    "year_match": year_ok,
                }
            )
            if name_ok:
                report["metrics"]["name_accuracy"] += 1
            if year_ok:
                report["metrics"]["year_accuracy"] += 1
            report["metrics"]["citation_recall"] += len(found_cits)

    # Actual-only clusters (not matched to any expected)
    for j, ac in enumerate(actual_clusters):
        if j in matched_actual_indices:
            continue
        report["actual_only"].append(
            {
                "case_name": _get_cluster_name(ac),
                "year": _get_cluster_year(ac),
                "citations": _get_cluster_citations(ac),
            }
        )

    return report


def print_extraction_report(report: Dict[str, Any]) -> None:
    """Print a human-readable comparison report."""
    m = report.get("metrics", {})
    exp_total = m.get("citation_expected_total", 0)
    recall = m.get("citation_recall", 0)
    exp_clusters = report.get("expected_cluster_count", 0)
    act_clusters = report.get("actual_cluster_count", 0)
    match_count = m.get("cluster_match_count", 0)
    name_acc = m.get("name_accuracy", 0)
    year_acc = m.get("year_accuracy", 0)

    print("=" * 60)
    print(f"EXTRACTION COMPARISON: {report.get('document_id', 'unknown')}")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  Expected clusters:   {exp_clusters}")
    print(f"  Actual clusters:     {act_clusters}")
    print(f"  Matched clusters:    {match_count}/{exp_clusters}")
    print(f"  Citation recall:     {recall}/{exp_total} expected citations found")
    print(f"  Name accuracy:       {name_acc}/{exp_clusters}")
    print(f"  Year accuracy:       {year_acc}/{exp_clusters}")
    print()

    mismatches = report.get("mismatches", [])
    if mismatches:
        print("MISMATCHES:")
        for i, mm in enumerate(mismatches[:15], 1):
            print(f"  [{i}] {mm.get('expected_case_name', 'N/A')}")
            print(f"      Expected year: {mm.get('expected_year')} | Actual: {mm.get('actual_year')}")
            print(f"      Name match: {mm.get('name_match')} | Year match: {mm.get('year_match')}")
            missing = mm.get("missing_citations", [])
            if missing:
                print(f"      Missing citations: {missing}")
        if len(mismatches) > 15:
            print(f"  ... and {len(mismatches) - 15} more")
        print()

    expected_only = report.get("expected_only", [])
    if expected_only:
        print("EXPECTED ONLY (not found in actual):")
        for i, eo in enumerate(expected_only[:10], 1):
            print(f"  {eo.get('expected_case_name')} | {eo.get('expected_citations')}")
        if len(expected_only) > 10:
            print(f"  ... and {len(expected_only) - 10} more")
        print()

    actual_only = report.get("actual_only", [])
    if actual_only:
        print("ACTUAL ONLY (no expected match):")
        for i, ao in enumerate(actual_only[:10], 1):
            print(f"  {ao.get('case_name')} | {ao.get('citations')[:3]}...")
        if len(actual_only) > 10:
            print(f"  ... and {len(actual_only) - 10} more")
        print()

    print("VERDICT:")
    if not mismatches and not expected_only:
        print("  PASS: All expected clusters matched.")
    elif expected_only and not mismatches:
        print(f"  PARTIAL: {match_count} matched, {len(expected_only)} expected clusters not found.")
    else:
        print(f"  FAIL: {len(mismatches)} mismatches, {len(expected_only)} expected-only.")
