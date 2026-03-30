"""
Compare pipeline output against human-reviewed expectations for saved brief PDFs.

Used by ``scripts/brief_goldens.py verify``. Manifest schema (``version`` 1):

``documents`` is a list of objects:

- ``file`` (str): PDF basename or path relative to ``--briefs-dir``.
- ``id`` (str, optional): stable id for error messages.
- ``enable_verification`` (bool, optional): override default for this document.
- ``expect`` (object):

  - ``min_extracted_chars`` / ``max_extracted_chars`` (int): raw text length from PDF.
  - ``min_citations`` / ``max_citations`` / ``exact_citation_count`` (int).
  - ``min_clusters`` / ``max_clusters`` / ``exact_cluster_count`` (int).
  - ``citation_substrings_required`` (list[str]): each substring must appear in at least one
    citation string (case-sensitive; normalize in manifest if needed).
  - ``citation_substrings_forbidden`` (list[str]): none may appear in any citation string.
  - ``cluster_rules`` (list[object]): each rule must be satisfied by **some** cluster.

    - ``all_citations_contain`` (list[str]): every string must appear in at least one **same**
      cluster member's ``citation`` field (single cluster).
    - ``any_citation_contains`` (list[str]): at least one cluster has a member whose citation
      contains **all** of these substrings (AND within one citation string).
    - ``case_name_contains`` (str): that cluster's ``cluster_case_name`` or any member
      ``extracted_case_name`` must contain this substring (case-insensitive).
"""

from __future__ import annotations

import re
from typing import Any


def _citation_display(c: Any) -> str:
    if isinstance(c, dict):
        return str(c.get("citation") or c.get("primary_citation") or "").strip()
    return str(getattr(c, "citation", None) or "").strip()


def _cluster_members(cluster: dict[str, Any]) -> list[dict[str, Any]]:
    raw = cluster.get("citations") or []
    out: list[dict[str, Any]] = []
    for x in raw:
        if isinstance(x, dict):
            out.append(x)
    return out


def verify_expectation(
    expect: dict[str, Any],
    *,
    text_length: int,
    citations: list[Any],
    clusters: list[dict[str, Any]],
) -> list[str]:
    """Return a list of human-readable errors; empty means pass."""
    errs: list[str] = []
    cit_strs = [_citation_display(c) for c in citations]
    cit_strs = [s for s in cit_strs if s]

    if "min_extracted_chars" in expect and text_length < int(expect["min_extracted_chars"]):
        errs.append(
            f"text length {text_length} < min_extracted_chars {expect['min_extracted_chars']}"
        )
    if "max_extracted_chars" in expect and text_length > int(expect["max_extracted_chars"]):
        errs.append(
            f"text length {text_length} > max_extracted_chars {expect['max_extracted_chars']}"
        )

    n_cit = len(cit_strs)
    if "exact_citation_count" in expect:
        want = int(expect["exact_citation_count"])
        if n_cit != want:
            errs.append(f"citation count {n_cit} != exact_citation_count {want}")
    else:
        if "min_citations" in expect and n_cit < int(expect["min_citations"]):
            errs.append(f"citation count {n_cit} < min_citations {expect['min_citations']}")
        if "max_citations" in expect and n_cit > int(expect["max_citations"]):
            errs.append(f"citation count {n_cit} > max_citations {expect['max_citations']}")

    n_cl = len(clusters)
    if "exact_cluster_count" in expect:
        want = int(expect["exact_cluster_count"])
        if n_cl != want:
            errs.append(f"cluster count {n_cl} != exact_cluster_count {want}")
    else:
        if "min_clusters" in expect and n_cl < int(expect["min_clusters"]):
            errs.append(f"cluster count {n_cl} < min_clusters {expect['min_clusters']}")
        if "max_clusters" in expect and n_cl > int(expect["max_clusters"]):
            errs.append(f"cluster count {n_cl} > max_clusters {expect['max_clusters']}")

    for sub in expect.get("citation_substrings_required") or []:
        if not any(sub in s for s in cit_strs):
            errs.append(f"no citation contains required substring {sub!r}")

    for sub in expect.get("citation_substrings_forbidden") or []:
        for s in cit_strs:
            if sub in s:
                errs.append(f"citation {s[:80]!r}... contains forbidden substring {sub!r}")
                break

    for ri, rule in enumerate(expect.get("cluster_rules") or []):
        if not _cluster_rule_satisfied(rule, clusters):
            errs.append(f"cluster_rules[{ri}] not satisfied: {rule!r}")

    return errs


def _cluster_matches_rule(cluster: dict[str, Any], rule: dict[str, Any]) -> bool:
    members = _cluster_members(cluster)
    cites = [_citation_display(m) for m in members if _citation_display(m)]
    blob_names = (cluster.get("cluster_case_name") or "") + " " + (cluster.get("case_name") or "")
    for m in members:
        blob_names += " " + str(m.get("extracted_case_name") or "")

    cnc = rule.get("case_name_contains")
    if cnc is not None and str(cnc).strip():
        if str(cnc).lower() not in blob_names.lower():
            return False

    ac = rule.get("any_citation_contains") or []
    if ac:
        if not any(all(sub in s for sub in ac) for s in cites):
            return False

    allc = rule.get("all_citations_contain") or []
    if allc:
        pool = " | ".join(cites)
        if not all(sub in pool for sub in allc):
            return False

    has_constraint = bool((cnc is not None and str(cnc).strip()) or ac or allc)
    if not has_constraint:
        return False
    return True


def _cluster_rule_satisfied(rule: dict[str, Any], clusters: list[dict[str, Any]]) -> bool:
    for cluster in clusters:
        if isinstance(cluster, dict) and _cluster_matches_rule(cluster, rule):
            return True
    return False


def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()
