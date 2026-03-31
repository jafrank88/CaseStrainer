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
  - ``citation_field_rules`` (list[object]): each rule must be satisfied by **at least one**
    flat citation whose display string contains ``citation_contains`` (substring match).

    - ``citation_contains`` (str, required): matched against each row's reporter/citation text.
    - ``verified`` (bool, optional): if present, must match that citation's verified flag.
    - ``canonical_name_contains`` (str, optional): case-insensitive substring of
      ``canonical_name`` / ``extracted_case_name`` combined.
    - ``canonical_year`` (str, optional): exact match after normalizing year from
      ``canonical_year`` or leading ``YYYY`` of ``canonical_date``.
    - ``canonical_url_contains`` (str, optional): substring of ``canonical_url`` and ``url``
      combined (case-sensitive; use lowercase URLs in rules if needed).
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


def _flat_citation_dicts(citations: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in citations:
        if isinstance(c, dict):
            out.append(c)
    return out


def _citation_verified_truthy(c: dict[str, Any]) -> bool:
    v = c.get("verified")
    if v is True or v == "true" or v == 1:
        return True
    if v is False or v == "false" or v == 0:
        return False
    return bool(v)


def _canonical_name_blob(c: dict[str, Any]) -> str:
    parts = (c.get("canonical_name"), c.get("extracted_case_name"))
    return " ".join(str(p or "") for p in parts)


def _citation_year_normalized(c: dict[str, Any]) -> str:
    cy = c.get("canonical_year")
    if cy is not None and str(cy).strip():
        return str(cy).strip()
    cd = str(c.get("canonical_date") or "").strip()
    m = re.match(r"^(\d{4})", cd)
    return m.group(1) if m else ""


def _citation_url_blob(c: dict[str, Any]) -> str:
    return f"{c.get('canonical_url') or ''} {c.get('url') or ''}"


def _citation_satisfies_field_rule(c: dict[str, Any], rule: dict[str, Any]) -> bool:
    needle = str(rule.get("citation_contains") or "")
    if not needle or needle not in _citation_display(c):
        return False

    if "verified" in rule and rule["verified"] is not None:
        want = bool(rule["verified"])
        if _citation_verified_truthy(c) != want:
            return False

    cnc = rule.get("canonical_name_contains")
    if cnc is not None and str(cnc).strip():
        if str(cnc).lower() not in _canonical_name_blob(c).lower():
            return False

    if "canonical_year" in rule and rule["canonical_year"] is not None:
        want_y = str(rule["canonical_year"]).strip()
        if want_y and _citation_year_normalized(c) != want_y:
            return False

    cuc = rule.get("canonical_url_contains")
    if cuc is not None and str(cuc).strip():
        if str(cuc) not in _citation_url_blob(c):
            return False

    return True


def _citation_field_rules_satisfied(
    rules: list[dict[str, Any]], citations: list[Any]
) -> tuple[bool, str]:
    flats = _flat_citation_dicts(citations)
    for ri, rule in enumerate(rules):
        cc = str(rule.get("citation_contains") or "").strip()
        if not cc:
            return False, f"citation_field_rules[{ri}] missing citation_contains"
        if not any(_citation_satisfies_field_rule(c, rule) for c in flats):
            return False, f"citation_field_rules[{ri}] no citation matched {rule!r}"
    return True, ""


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

    cfr = expect.get("citation_field_rules") or []
    if cfr:
        ok, msg = _citation_field_rules_satisfied(cfr, citations)
        if not ok:
            errs.append(msg)

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
