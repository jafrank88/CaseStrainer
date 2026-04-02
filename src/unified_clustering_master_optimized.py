"""
Minimal fast clustering fallback - groups citations simply and quickly.

Parallel citations (same case, multiple reporters) should appear in one cluster.
If the doc cites A & B and later B & C, transitive merge puts A, B, C in one cluster.
"""
# Bump when clustering logic changes so API/workers can report which version ran
CLUSTERING_VERSION = "2026-03-v7"

import re
import logging
import time
from typing import Dict, Any, List, Set, Tuple, Optional

from src.utils.same_case import names_are_same_case
from src.utils.cluster_filter import citation_conflicts_with_group, _extract_year
from src.clustering.detection import _clean_ecn, _same_case_check

logger = logging.getLogger(__name__)


def _federal_reporter_primary_key(cit: str) -> str:
    """Same volume + reporter family + first page => one cluster key (pins drop , 2227 etc.)."""
    if not (cit or "").strip():
        return ""
    s = re.sub(r"\s+", " ", str(cit).strip())
    m = re.search(
        r"\b(\d+)\s+"
        r"(U\.?\s*S\.?|S\.?\s*Ct\.?|L\.?\s*Ed\.?\s*(?:2d)?|"
        r"F\.?\s*Supp\.?\s*(?:2d|3d)?|F\.?\s*3d|F\.?\s*2d|F\.?\s*4th)\s+"
        r"(\d+)\b",
        s,
        re.IGNORECASE,
    )
    if not m:
        return ""
    rep = re.sub(r"\s+", "", m.group(2).lower())
    return f"{m.group(1)}:{rep}:{m.group(3)}"


def _paren_decision_year_from_cit(cit: str) -> Optional[str]:
    """Align with UnifiedCitationProcessorV2._decision_year_from_citation_paren (no import cycle)."""
    if not (cit or "").strip():
        return None
    main = str(cit).strip()
    for sep in ("(quoting ", "(citing ", "(quoted in ", "(cited in "):
        ix = main.find(sep)
        if ix != -1:
            main = main[:ix].strip()
            break
    if re.search(r"\((?:scotus|ca\d+)\s+(?:19|20)\d{2}\s*\)", main, re.IGNORECASE):
        return None
    best: Optional[str] = None
    for m in re.finditer(r"\(([^)]*)\)", main):
        inner = m.group(1) or ""
        ym = re.search(r"\b((?:17|18|19|20)\d{2})\b", inner)
        if ym:
            y = int(ym.group(1))
            if 1700 <= y <= 2030:
                best = ym.group(1)
    return best


def _trailing_paren_year_from_cit(cit: str) -> Optional[str]:
    """
    Extract the decision year from the *final* parenthetical right after the citation.

    This matches the most common Bluebook pattern used in briefs:
      `... 900 F.2d 566 (2d Cir. 1990)`  -> 1990
      `... 347 U.S. 521 (1954)`         -> 1954

    We intentionally ignore nested "(quoting ...)" / "(citing ...)" segments since they
    often contain years for *other* cases.
    """
    if not (cit or "").strip():
        return None
    main = str(cit).strip()
    for sep in ("(quoting ", "(citing ", "(quoted in ", "(cited in "):
        ix = main.find(sep)
        if ix != -1:
            main = main[:ix].strip()
            break
    # Ignore our synthetic suffixes like "(scotus 1954)".
    if re.search(r"\((?:scotus|ca\d+)\s+(?:19|20)\d{2}\s*\)\s*$", main, re.IGNORECASE):
        return None
    m = re.search(r"\(([^)]*?)\)\s*$", main)
    if not m:
        return None
    inner = m.group(1) or ""
    ym = re.search(r"\b((?:17|18|19|20)\d{2})\b", inner)
    if not ym:
        return None
    y = int(ym.group(1))
    return ym.group(1) if 1700 <= y <= 2030 else None


def _get_citation_key(c: Dict[str, Any]) -> str:
    """Stable key for a citation dict. Normalize state reporter variants so
    e.g. 166 Wash. 2d 264 and 166 Wn.2d 264 merge (same case, same reporter)."""
    raw = (c.get("citation") or c.get("text") or str(c)).strip()
    if not raw:
        return raw
    # Normalize Washington reporter abbreviations to one form for merge/key purposes
    key = re.sub(r"\bWash\.\s*2d\b", "Wn.2d", raw, flags=re.IGNORECASE)
    key = re.sub(r"\bWash\.\s*App\.\s*2d\b", "Wn. App. 2d", key, flags=re.IGNORECASE)
    key = re.sub(r"\s+", " ", key).strip()
    return key


def _merge_groups_transitive(groups_list: List[List[Dict[str, Any]]]) -> List[List[Dict[str, Any]]]:
    """
    Merge groups that share at least one citation (transitive closure).
    Same goal as full clustering: A & B here, B & C later => one cluster with A, B, C.
    Uses Union-Find for O(g * alpha(g)) instead of O(g^3) iterative merge.
    """
    if not groups_list or len(groups_list) <= 1:
        return groups_list

    n = len(groups_list)
    parent = list(range(n))

    def find(x: int) -> int:
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    def years_of(g: List[Dict[str, Any]]) -> Set[int]:
        return {y for c in g for y in (_extract_year(c),) if y is not None}

    def _same_canonical_name(i: int, j: int) -> bool:
        """True if both groups have verified citations with same canonical_name (e.g. CFE I + CFE II)."""
        def names_from_group(g: List[Dict[str, Any]]) -> Set[str]:
            out = set()
            for c in g:
                cn = (c.get("canonical_name") or c.get("extracted_case_name") or "").strip()
                if cn and " v. " in cn:
                    out.add(cn.lower())
            return out
        ci, cj = names_from_group(groups_list[i]), names_from_group(groups_list[j])
        if not ci or not cj:
            return False
        return bool(ci & cj) or any(names_are_same_case(a, b) for a in ci for b in cj)

    def has_year_conflict(i: int, j: int) -> bool:
        yi, yj = years_of(groups_list[i]), years_of(groups_list[j])
        if not yi or not yj:
            return False
        # When same canonical case (e.g. CFE I 1995 + CFE II 2003), allow merge
        if _same_canonical_name(i, j):
            return False
        return any(abs((a or 0) - (b or 0)) > 2 for a in yi for b in yj)

    # Build citation_key -> list of (group_idx, citation_dict) and per-group key set
    key_to_pairs: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
    key_sets_by_group: Dict[int, Set[str]] = {}
    for i, g in enumerate(groups_list):
        if not g:
            continue
        key_sets_by_group[i] = set()
        for c in g:
            k = _get_citation_key(c)
            if k:
                key_to_pairs.setdefault(k, []).append((i, c))
                key_sets_by_group[i].add(k)

    def _name(c: Dict[str, Any]) -> str:
        return (c.get("canonical_name") or c.get("extracted_case_name") or c.get("case_name") or "").strip() or ""

    # Merge only when the same *exact* key appears in both groups and the citations with that key refer to the same case
    for _key, pairs in key_to_pairs.items():
        # Pairs are (group_idx, citation_dict); collect unique group indices and one citation per group for name check
        group_to_citation: Dict[int, Dict[str, Any]] = {}
        for i, c in pairs:
            group_to_citation[i] = c  # last citation with this key in group i
        ids = list(group_to_citation.keys())
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                i, j = ids[a], ids[b]
                if find(i) == find(j):
                    continue
                if has_year_conflict(i, j):
                    continue
                # Same exact key: only merge if the citations with this key in each group refer to the same case
                ci, cj = group_to_citation[i], group_to_citation[j]
                ni, nj = _name(ci), _name(cj)
                if ni and nj and not names_are_same_case(ni, nj):
                    logger.debug(
                        f"[MINIMAL-CLUSTER] Skip union groups {i},{j} (share key but different case: '{ni[:30]}' vs '{nj[:30]}')"
                    )
                    continue
                union(i, j)
                logger.debug(
                    f"[MINIMAL-CLUSTER] Union groups {i},{j} (share citation)"
                )

    # Phase 2 (Kustura): merge groups that share no citation key but are same case (e.g. 169 Wn.2d 81 in one
    # group and 233 P.3d 853 in another — parallel citations with cleaned name match via _same_case_check).
    for i in range(n):
        if not groups_list[i]:
            continue
        for j in range(i + 1, n):
            if not groups_list[j]:
                continue
            if find(i) == find(j):
                continue
            ki = key_sets_by_group.get(i, set())
            kj = key_sets_by_group.get(j, set())
            if ki & kj:
                continue  # already merged in phase 1
            if has_year_conflict(i, j):
                continue
            if not any(
                _same_case_check(ci, cj)
                for ci in groups_list[i] for cj in groups_list[j]
            ):
                continue
            conflict = any(
                citation_conflicts_with_group(c, groups_list[j])
                for c in groups_list[i]
            ) or any(
                citation_conflicts_with_group(c, groups_list[i])
                for c in groups_list[j]
            )
            if conflict:
                continue
            union(i, j)
            logger.debug(
                f"[MINIMAL-CLUSTER] Union groups {i},{j} (no shared key, same case e.g. Kustura Wn.2d+P.3d)"
            )

    # Third pass: merge groups with same canonical case (e.g. CFE I 86 N.Y.2d 307 + CFE II 100 N.Y.2d 893)
    # even when they don't share a citation. Different extracted names ("Fiscal Equity v. State" vs
    # "Campaign for Fiscal Equity, Inc. v. State") can split them initially.
    # Do NOT merge when citations conflict (e.g. same reporter, different volumes = different cases:
    # 67 S.E.2d 289 (1951) vs 431 S.E.2d 289 (1993)).
    for i in range(n):
        if not groups_list[i]:
            continue
        for j in range(i + 1, n):
            if not groups_list[j]:
                continue
            if find(i) != find(j) and _same_canonical_name(i, j) and not has_year_conflict(i, j):
                # Block merge if any citation in group i conflicts with group j (or vice versa)
                conflict = any(
                    citation_conflicts_with_group(c, groups_list[j])
                    for c in groups_list[i]
                ) or any(
                    citation_conflicts_with_group(c, groups_list[i])
                    for c in groups_list[j]
                )
                if not conflict:
                    union(i, j)
                    logger.debug(
                        f"[MINIMAL-CLUSTER] Union groups {i},{j} (same canonical case)"
                    )

    # Collapse by root; O(g)
    root_to_citations: Dict[int, List[Dict[str, Any]]] = {}
    seen_keys: Dict[int, Set[str]] = {}
    for i in range(n):
        if not groups_list[i]:
            continue
        r = find(i)
        if r not in root_to_citations:
            root_to_citations[r] = []
            seen_keys[r] = set()
        for c in groups_list[i]:
            k = _get_citation_key(c)
            if k not in seen_keys[r]:
                seen_keys[r].add(k)
                root_to_citations[r].append(c)

    return list(root_to_citations.values())


def _reassign_bare_citations_by_containment(
    groups_list: List[List[Dict[str, Any]]],
) -> List[List[Dict[str, Any]]]:
    """
    Move citations whose text is a bare reporter (e.g. "857 N.W.2d 569") from group A
    to group B when that text appears as substring in a citation in group B **and** the
    containing citation refers to the same case (by extracted/canonical name).
    Prevents moving e.g. "587 U.S. 262" (Students for Fair Admissions) into a group
    that only contains it inside "(citing SFA, 587 U.S. 262)" under a different case.
    """
    if len(groups_list) < 2:
        return groups_list

    def get_text(c: Dict[str, Any]) -> str:
        return (c.get("citation") or c.get("text") or "").strip()

    def get_name(c: Dict[str, Any]) -> str:
        return (c.get("canonical_name") or c.get("extracted_case_name") or c.get("case_name") or "").strip() or ""

    bare_pattern = re.compile(r"\d+\s+[A-Z]\.?\s*[A-Za-z0-9\.]+\s+\d+")

    # Build list (group_idx, citation_dict, citation_text) for containment + name check
    other_entries: List[Tuple[int, Dict[str, Any], str]] = []
    for j, group in enumerate(groups_list):
        if not group:
            continue
        for oc in group:
            ot = get_text(oc)
            if ot:
                other_entries.append((j, oc, ot))

    # Single pass: collect moves only when target citation is same case as bare citation
    moves: List[Tuple[Dict[str, Any], int, int]] = []
    for i, group in enumerate(groups_list):
        if not group:
            continue
        for cit in group:
            cit_text = get_text(cit)
            if not cit_text or len(cit_text) > 45:
                continue
            if not bare_pattern.search(cit_text):
                continue
            bare_name = get_name(cit)
            for j, oc, oc_text in other_entries:
                if j == i:
                    continue
                if cit_text not in oc_text or cit_text == oc_text:
                    continue
                # Only reassign when the citation that contains this bare string
                # refers to the same case (avoids mixing e.g. SFA into Cochise cluster)
                target_name = get_name(oc)
                if bare_name and target_name:
                    if not names_are_same_case(bare_name, target_name):
                        logger.debug(
                            f"[MINIMAL-CLUSTER] Skip reassign bare '{cit_text[:40]}' to group {j}: "
                            f"bare name '{bare_name[:30]}' vs target '{target_name[:30]}'"
                        )
                        continue
                elif bare_name and not target_name:
                    # Bare has a name, target citation has no name - don't move into unnamed
                    continue
                moves.append((cit, i, j))
                logger.debug(
                    f"[MINIMAL-CLUSTER] Reassign bare cite '{cit_text}' to group {j} (same case)"
                )
                break

    # Apply moves; O(moves)
    for cit, from_i, to_j in moves:
        try:
            groups_list[from_i].remove(cit)
            groups_list[to_j].append(cit)
        except ValueError:
            pass

    return [g for g in groups_list if g]


def _extract_case_name_from_citation_text(citation_text: str) -> str:
    """Extract 'Party v. Party' from the citation text itself (not metadata)."""
    if not citation_text:
        return ""
    # Match "State ex rel. Name v. Name" first (e.g. State ex rel. Oriana House, Inc. v. Montgomery)
    m = re.match(
        r"^(State\s+ex\s+rel\.\s+(?:[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)"
        r"(?:,\s*[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)*\s+v\.\s+"
        r"(?:[A-Z][A-Za-z'\-]+\.?(?:[\s,]+[A-Za-z'\-]+\.?)*))",
        citation_text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip().rstrip(",").lower()
    # Match "Name v. Name" before the volume number, handling commas in names
    # e.g., "Trichell v. Midland Credit Mgmt., Inc., 964 F.3d 990"
    m = re.match(
        r"^((?:[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)"
        r"(?:,\s*[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)*\s+v\.\s+"
        r"(?:[A-Z][A-Za-z'\-]+\.?(?:[\s,]+[A-Za-z'\-]+\.?)*))",
        citation_text,
    )
    if m:
        return m.group(1).strip().rstrip(",").lower()
    return ""


def _extract_case_name_with_case_from_citation_text(citation_text: str) -> str:
    """Extract case name with original case for display (e.g. 'State ex rel. Oriana House')."""
    if not citation_text:
        return ""
    # Match "State ex rel. Name v. Name" first
    m = re.match(
        r"^(State\s+ex\s+rel\.\s+(?:[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)"
        r"(?:,\s*[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)*\s+v\.\s+"
        r"(?:[A-Z][A-Za-z'\-]+\.?(?:[\s,]+[A-Za-z'\-]+\.?)*))",
        citation_text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip().rstrip(",")
    m = re.match(
        r"^((?:[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)"
        r"(?:,\s*[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)*\s+v\.\s+"
        r"(?:[A-Z][A-Za-z'\-]+\.?(?:[\s,]+[A-Za-z'\-]+\.?)*))",
        citation_text,
    )
    if m:
        return m.group(1).strip().rstrip(",")
    return ""


def _normalize_canonical_url(url: str) -> str:
    """Stable key for grouping by verified opinion (same URL = same case)."""
    if not url or not isinstance(url, str):
        return ""
    u = url.strip().rstrip("/")
    return u if u.startswith("http") else ""


def cluster_citations_minimal(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ultra-fast minimal clustering - group by same case (names_are_same_case) or citation text.
    Parallel citations (same case, different reporters) are kept together by:
    1. Grouping by canonical_url when present (same verified opinion URL = same cluster).
    2. Then name-based grouping and transitive merge for the rest.
    Handles "Lloyd's of London Pope Res., LP" vs "Pope Res., LP" as same case.
    Complexity: O(n * g) where g = number of groups.
    """
    if not citations:
        return []

    # Group by same case: (representative_key, [citations])
    groups: List[tuple[str, List[Dict[str, Any]]]] = []
    no_name_groups: Dict[str, List[Dict[str, Any]]] = {}  # O(1) lookup for bare citations
    # Same canonical_url => same opinion => one cluster (best way to keep parallel citations together)
    url_to_group_index: Dict[str, int] = {}
    cite_pk_to_group: Dict[str, int] = {}

    for citation in citations:
        citation_text = str(citation.get("citation") or "").strip()
        rep_pk = _federal_reporter_primary_key(citation_text)
        if rep_pk and rep_pk in cite_pk_to_group:
            groups[cite_pk_to_group[rep_pk]][1].append(citation)
            continue

        # 1) Group by canonical_url when present (verified parallel citations share the same opinion URL)
        canonical_url = citation.get("canonical_url") or ""
        url_key = _normalize_canonical_url(canonical_url)
        if url_key:
            if url_key in url_to_group_index:
                gi = url_to_group_index[url_key]
                groups[gi][1].append(citation)
                if rep_pk:
                    cite_pk_to_group[rep_pk] = gi
                continue
            rep_key = (
                citation.get("canonical_name")
                or citation.get("extracted_case_name")
                or citation.get("case_name")
                or url_key
            )
            groups.append((rep_key, [citation]))
            idx = len(groups) - 1
            url_to_group_index[url_key] = idx
            if rep_pk:
                cite_pk_to_group[rep_pk] = idx
            continue

        # 2) No canonical_url: use name-based grouping (extracted, case_name, or canonical for reporter-only)
        case_name = (
            citation.get("extracted_case_name")
            or citation.get("case_name")
            or citation.get("canonical_name")
        )

        # FIX 2026-02-10: Cross-check that the citation text doesn't contain
        # a DIFFERENT case name than the metadata.  Use citation text name when they conflict.
        cit_text_name = _extract_case_name_from_citation_text(citation_text)
        if cit_text_name and " v. " in cit_text_name and case_name and case_name != "N/A" and " v. " in case_name:
            key_first = (case_name or "").split(" v. ")[0].strip().split()[-1].lower()
            cit_first = cit_text_name.split(" v. ")[0].strip().split()[-1].lower()
            if key_first and cit_first and key_first != cit_first:
                logger.info(
                    f"[MINIMAL-CLUSTER] Citation text name '{cit_text_name}' differs from "
                    f"metadata name '{case_name}' - using citation text for grouping"
                )
                case_name = cit_text_name

        if case_name and case_name != "N/A":
            # Find existing group where names_are_same_case(case_name, group_rep).
            # Use cleaned names so contaminated extracted_case_name (e.g. "Kustura v. X, 169 Wn. 2d 81")
            # matches "Kustura v. X, 233 P.3d 853" — works for any legal doc with parallel cites.
            case_name_clean = _clean_ecn(case_name) or case_name
            matched = False
            for i, (rep_key, group_cits) in enumerate(groups):
                rep_name = (
                    group_cits[0].get("extracted_case_name")
                    or group_cits[0].get("case_name")
                    or group_cits[0].get("canonical_name")
                    or rep_key
                )
                rep_name_clean = _clean_ecn(rep_name) if rep_name else rep_name
                if names_are_same_case(case_name_clean, rep_name_clean) and not citation_conflicts_with_group(citation, group_cits):
                    group_cits.append(citation)
                    if rep_pk:
                        cite_pk_to_group[rep_pk] = i
                    matched = True
                    break
            if not matched:
                groups.append((case_name, [citation]))
                idx = len(groups) - 1
                if rep_pk:
                    cite_pk_to_group[rep_pk] = idx
        else:
            # No case name: O(1) dict lookup instead of O(g) scan
            key = citation_text
            no_name_groups.setdefault(key, []).append(citation)

    # Merge no-name groups into main list (join existing reporter-primary group if any member matches)
    for key, cits in no_name_groups.items():
        merge_idx: Optional[int] = None
        for c in cits:
            pk2 = _federal_reporter_primary_key(str(c.get("citation") or "").strip())
            if pk2 and pk2 in cite_pk_to_group:
                merge_idx = cite_pk_to_group[pk2]
                break
        if merge_idx is not None:
            groups[merge_idx][1].extend(cits)
        else:
            groups.append((key, cits))
            idx = len(groups) - 1
            for c in cits:
                pk2 = _federal_reporter_primary_key(str(c.get("citation") or "").strip())
                if pk2:
                    cite_pk_to_group[pk2] = idx

    # Transitive merge: groups that share a citation (e.g. A&B and B&C) become one cluster
    groups_list = [g for _, g in groups]
    before = len(groups_list)
    groups_list = _merge_groups_transitive(groups_list)
    if len(groups_list) < before:
        logger.info(
            f"[MINIMAL-CLUSTER] Transitive merge: {before} groups -> {len(groups_list)} "
            "(parallel groups sharing a citation merged)"
        )

    # Reassign bare citations (e.g. "857 N.W.2d 569") to group whose citation contains them
    groups_list = _reassign_bare_citations_by_containment(groups_list)

    # Create simple clusters from (possibly merged) groups
    clusters = []
    for i, group_citations in enumerate(groups_list, 1):
        # Get best name from group - prefer name that appears in citation text (avoids Hearst bleed)
        best_name = None
        best_year = None
        any_verified = False
        names_from_cit_text_with_case: List[Tuple[str, str]] = []  # (lower, original)

        for c in group_citations:
            name = c.get("extracted_case_name") or c.get("case_name")
            canonical = c.get("canonical_name") or ""
            cit_text = (c.get("citation") or "").strip()
            if cit_text:
                ct_name = _extract_case_name_from_citation_text(cit_text)
                ct_name_orig = _extract_case_name_with_case_from_citation_text(cit_text)
                if ct_name and " v. " in ct_name and ct_name_orig:
                    names_from_cit_text_with_case.append((ct_name, ct_name_orig))
            # Prefer canonical_name when it's more specific (e.g. "State ex rel. Oriana House" vs "Hearst")
            if canonical and " v. " in canonical and "state ex rel" in canonical.lower():
                names_from_cit_text_with_case.append(
                    (canonical.lower(), canonical)
                )
            if name and name != "N/A" and not best_name:
                best_name = name
            year = c.get("extracted_date") or c.get("canonical_date")
            if year and year != "N/A" and not best_year:
                best_year = year
            if c.get("verified"):
                any_verified = True

        # Year preference: when group has multiple years, prefer the one NOT from nested (citing...)
        # and prefer more recent when reporter suggests recent case (e.g. 857 N.W.2d 569 = 2015, not 1981)
        # Also prefer year from bare reporter cite (shortest text) - it comes from immediate doc context
        year_candidates: List[Tuple[str, str, bool, int]] = []  # (year, citation_snippet, has_citing, len)
        for c in group_citations:
            y = c.get("extracted_date") or c.get("canonical_date")
            if not y or y == "N/A":
                continue
            ct = (c.get("citation") or "")[:120]
            has_citing = "(citing" in ct.lower()
            year_candidates.append((str(y).strip(), ct, has_citing, len(ct)))
        if year_candidates:
            # Prefer year from citation that does NOT contain "(citing" (nested citation year)
            clean = [t for t in year_candidates if not t[2]]
            candidates = clean if clean else year_candidates

            def _year_int(t):
                try:
                    m = re.search(r"(19|20)\d{2}", str(t[0]))
                    return int(m.group(0)) if m else 0
                except (AttributeError, ValueError):
                    return 0

            # Primary rule (by far the most common): use the year in the final parenthetical
            # right after the citation text: `(.... ####)`.
            trailing_years = [
                _trailing_paren_year_from_cit((c.get("citation") or "")) for c in group_citations
            ]
            trailing_years = [y for y in trailing_years if y]
            if trailing_years:
                # Choose the most common trailing year within the group (robust to one-off contamination).
                counts: Dict[str, int] = {}
                for y in trailing_years:
                    counts[y] = counts.get(y, 0) + 1
                best_year = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            else:
                # Secondary: if the group has multiple plausible years, avoid "prefer max year" here.
                # That heuristic amplifies cross-case bleed; instead prefer citation-paren years when
                # unambiguous, otherwise prefer the year from the shortest citation mention.
                paren_years = [
                    _paren_decision_year_from_cit((c.get("citation") or ""))
                    for c in group_citations
                ]
                paren_years = [y for y in paren_years if y]
                if paren_years and len(set(paren_years)) == 1:
                    best_year = paren_years[0]
                else:
                    candidates_sorted = sorted(candidates, key=lambda t: t[3])
                    best_year = candidates_sorted[0][0]

        # Prefer name from citation text over metadata (avoids Hearst/prior-citation bleed)
        # CRITICAL: Prefer canonical_name with "State ex rel." when present (avoids Hearst bleed)
        state_ex_rel_canonical = None
        for c in group_citations:
            can = (c.get("canonical_name") or "").strip()
            if can and "state ex rel" in can.lower() and " v. " in can:
                state_ex_rel_canonical = can
                break
        if state_ex_rel_canonical:
            best_name = state_ex_rel_canonical
        elif names_from_cit_text_with_case:
            best_from_text = max(names_from_cit_text_with_case, key=lambda x: len(x[1]))[1]
            best_name = best_from_text

        cluster_key = (best_name or (group_citations[0].get("citation", "") if group_citations else ""))[:200]
        cluster = {
            "cluster_id": f"cluster_{i}",
            "cluster_key": cluster_key,
            "citations": group_citations,
            "size": len(group_citations),
            "cluster_case_name": best_name or "Unknown Case",
            "cluster_year": best_year,
            "extracted_case_name": best_name,
            "extracted_date": best_year,
            "canonical_name": group_citations[0].get("canonical_name") if group_citations else None,
            "canonical_date": group_citations[0].get("canonical_date") if group_citations else None,
            "cluster_members": [c.get("citation", "") for c in group_citations],
            "confidence": 0.8 if len(group_citations) > 1 else 0.5,
            "verified": any_verified,
            "verification_status": "verified" if any_verified else "not_verified",
            "metadata": {"created_by": "minimal_clustering"},
        }
        clusters.append(cluster)

    logger.info(f"[MINIMAL-CLUSTER] Created {len(clusters)} clusters from {len(citations)} citations")
    return clusters


def cluster_citations_optimized(
    citations, original_text: str = "", enable_verification: bool = False, request_id: str = ""
):
    """
    Entry point that uses minimal clustering for speed
    """
    start = time.time()

    # Convert objects to dicts if needed
    citation_dicts = []
    for c in citations:
        if isinstance(c, dict):
            citation_dicts.append(c)
        elif hasattr(c, "__dict__"):
            citation_dicts.append(c.__dict__)
        else:
            citation_dicts.append({"citation": str(c)})

    result = cluster_citations_minimal(citation_dicts)

    elapsed = time.time() - start
    logger.info(f"[OPTIMIZED-CLUSTER] Completed in {elapsed:.3f}s: {len(result)} clusters")
    return result
