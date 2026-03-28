"""
Response enrichment for Vue API: display_base_citation, fallback clusters,
citation score/similarity, and cluster_sections. Keeps vue_api_endpoints_updated.py lean.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from src.utils.verification_display_utils import (
    has_canonical_url,
    is_effectively_verified_citation,
    citation_core_key,
    is_proprietary_citation,
)

logger = logging.getLogger(__name__)


def extract_display_base_citation(text: Optional[str]) -> Optional[str]:
    """
    Extract base reporter citation (e.g. "422 U.S. 490") from full citation text.
    Port of frontend extractBaseReporterCitation() for single source of truth.
    """
    if not text or not isinstance(text, str):
        return None
    t = text.strip()
    if not t:
        return None

    specific_patterns = [
        (r"(\d+)\s+(Wn\.\s*App\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(Wash\.\s*App\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(Wn\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(Wash\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(F\.\s*Supp\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(F\.\s*Supp\.)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(F\.\s*R\.\s*D\.)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(L\.\s*Ed\.\s*2d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(S\.\s*Ct\.)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(F\.\s*App['\u2019]?x\.?)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(Fed\.\s*App['\u2019]?x\.?)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(F\.[234](?:th|d))\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(A\.[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(So\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(N\.\s*[EW]\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(S\.\s*[EW]\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(P\.[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(Cal\.\s*(?:App\.\s*)?[234](?:th|d))\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(Ohio\s+App\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(N\.Y\.S\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(A\.D\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
        (r"(\d+)\s+(N\.Y\.\s*[23]d)\s+(\d+)", r"\1 \2 \3"),
    ]
    for pattern, repl in specific_patterns:
        m = re.search(pattern, t, re.IGNORECASE)
        if m:
            return f"{m.group(1)} {m.group(2).strip()} {m.group(3)}"

    wl = re.search(r"(\d{4})\s+(WL|U\.?\s*S\.?\s*LEXIS|LEXIS)\s+(\d+)", t, re.IGNORECASE)
    if wl:
        return f"{wl.group(1)} {wl.group(2).strip()} {wl.group(3)}"

    generic = re.search(r"(\d+)\s+([A-Za-z][A-Za-z.\s]+?(?:\d+[a-z]{0,2})?)\s+(\d+)", t)
    if generic:
        return f"{generic.group(1)} {generic.group(2).strip()} {generic.group(3)}"
    return None


def _citation_display_merge_key(c: Dict[str, Any]) -> str:
    """
    Key for merging duplicate display rows (e.g. 171 Wash. 2d 486 vs 171 Wn.2d 486).
    Uses citation_core_key so abbreviation variants collapse; empty if unparseable.
    """
    raw = (c.get("citation") or c.get("text") or "").strip()
    base = (c.get("display_base_citation") or extract_display_base_citation(raw) or "").strip()
    if base:
        k = citation_core_key(base)
        if k:
            return k
    if raw:
        k = citation_core_key(raw)
        if k:
            return k
    return ""


def compute_citation_score_and_similarity(c: Dict[str, Any]) -> Tuple[int, float]:
    """
    Port of frontend useCitationNormalization: score 0-5 and name similarity 0.0-1.0.
    Returns (score, name_similarity).
    """
    score = 0
    canonical = (c.get("canonical_name") or "").strip()
    extracted = (c.get("extracted_case_name") or "").strip()
    if canonical and canonical != "N/A":
        score += 2
    if extracted and extracted != "N/A" and canonical and canonical != "N/A":
        cw = [w for w in canonical.lower().split() if len(w) > 2]
        ew = [w for w in extracted.lower().split() if len(w) > 2]
        if cw or ew:
            common = len([x for x in cw if x in ew])
            sim = common / max(len(cw), len(ew)) if (cw or ew) else 0.0
            if sim >= 0.5:
                score += 1
        else:
            sim = 1.0 if canonical == extracted else 0.0
    else:
        sim = 0.0

    if c.get("canonical_date") and str(c.get("canonical_date", "")).strip() != "N/A":
        score += 1
    if c.get("canonical_url") or c.get("url"):
        u = (c.get("canonical_url") or c.get("url") or "").strip()
        if u:
            score += 1

    # name_similarity for API (extracted vs canonical word overlap)
    if not canonical or canonical == "N/A":
        name_similarity = 0.0
    elif not extracted or extracted == "N/A":
        name_similarity = 0.0
    else:
        cw = [w for w in canonical.lower().split() if len(w) > 2]
        ew = [w for w in extracted.lower().split() if len(w) > 2]
        if not cw and not ew:
            name_similarity = 1.0
        else:
            common = len([x for x in cw if x in ew])
            name_similarity = common / max(len(cw), len(ew))

    return (min(score, 5), name_similarity)


def build_fallback_clusters(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build clusters from flat citations when the pipeline returns no clusters.
    Matches frontend logic: group by canonical_url (>=2), then by parallel key (>=2), then singletons.
    """
    if not citations:
        return []

    used = set()
    groups: List[List[Dict[str, Any]]] = []

    by_url: Dict[str, List[int]] = {}
    for i, c in enumerate(citations):
        u = (c.get("canonical_url") or "").strip()
        if u:
            by_url.setdefault(u, []).append(i)

    for idxs in by_url.values():
        if len(idxs) >= 2:
            groups.append([citations[j] for j in idxs])
            used.update(idxs)

    by_parallel: Dict[str, List[int]] = {}
    for i, c in enumerate(citations):
        if i in used:
            continue
        pc = c.get("parallel_citations") or []
        if pc:
            cit_text = str(c.get("citation") or c.get("text") or "")
            key_parts = [cit_text] + [str(p) for p in pc]
            key_parts.sort()
            key = "|".join(key_parts)
            by_parallel.setdefault(key, []).append(i)

    for idxs in by_parallel.values():
        if len(idxs) >= 2:
            groups.append([citations[j] for j in idxs])
            used.update(idxs)

    for i, c in enumerate(citations):
        if i not in used:
            groups.append([c])

    out = []
    for idx, g in enumerate(groups):
        rep = next((x for x in g if (x.get("canonical_name") or "").strip()), g[0])
        has_name = any((c.get("name_mismatch") is True for c in g))
        has_date = any((c.get("date_mismatch") is True for c in g))
        sub_name = "N/A"
        for x in g:
            en = (x.get("extracted_case_name") or "").strip()
            if en and en != "N/A":
                sub_name = en
                break
        sub_date = "N/A"
        for x in g:
            ed = (x.get("extracted_date") or "").strip()
            if ed and ed != "N/A":
                sub_date = ed
                break
        # When canonical URL exists, use only canonical_date - never extracted_date (avoids hiding date mismatch)
        ver_date_val = rep.get("canonical_date") if rep.get("canonical_url") else (rep.get("canonical_date") or rep.get("extracted_date"))
        raw_date = (str(ver_date_val or "").strip()) or "N/A"
        from src.utils.date_utils import extract_year_value
        ver_date = extract_year_value(raw_date) or raw_date if raw_date != "N/A" else "N/A"
        cluster = {
            "cluster_id": f"fallback_{idx + 1}",
            "citations": g,
            "verifying_display_name": (rep.get("canonical_name") or "").strip() or "N/A",
            "verifying_display_date": ver_date,
            "submitted_display_name": sub_name,
            "submitted_display_date": sub_date,
            "has_name_mismatch": has_name,
            "has_date_mismatch": has_date,
        }
        out.append(cluster)
    return out


def _fuller_citation_match(short: str, candidate: str) -> bool:
    """
    True if candidate is a fuller version of short (short is prefix, candidate has valid base).
    E.g. short="31 Wn. App. 2", candidate="31 Wn. App. 2d 100, 110".
    """
    if not short or not candidate or len(candidate) <= len(short):
        return False
    s = short.strip()
    c = candidate.strip()
    if not c.startswith(s):
        return False
    # Candidate must have a proper base (volume reporter page) - ensures it's not also truncated
    base = extract_display_base_citation(candidate)
    if not base:
        return False
    # Reject if base is same as short (e.g. both parse to "31 Wn. App. 2" - short is not really truncated)
    return len(base) > len(s)


def enrich_citations_with_cluster_members(
    citations: List[Dict[str, Any]], cluster_members: List[Any]
) -> List[Dict[str, Any]]:
    """
    Replace truncated citation text with fuller text from cluster_members.
    E.g. citation "31 Wn. App. 2" -> "31 Wn. App. 2d 100, 110" when cluster_members has the full one.

    Also adds citation objects for cluster_members that have distinct display_base_citation
    and aren't already in citations (e.g. parallel citations like 517 U.S., 116 S. Ct., 134 L. Ed. 2d).
    """
    if not cluster_members:
        return list(citations) if citations else []
    member_texts = []
    for m in cluster_members:
        if isinstance(m, str) and m.strip():
            member_texts.append(m.strip())
        elif isinstance(m, dict):
            ct = (m.get("citation") or m.get("text") or "").strip()
            if ct:
                member_texts.append(ct)
    if not member_texts:
        return list(citations) if citations else []

    out = []
    if citations:
        for c in citations:
            c = dict(c)
            raw = (c.get("citation") or c.get("text") or "").strip()
            if not raw:
                out.append(c)
                continue
            for mt in member_texts:
                if _fuller_citation_match(raw, mt):
                    c["citation"] = mt
                    if "text" in c:
                        c["text"] = mt
                    base = extract_display_base_citation(mt)
                    if base:
                        c["display_base_citation"] = base
                    break
            out.append(c)

    # Add parallel citations from cluster_members that aren't already represented.
    # E.g. BMW: 517 U.S. 559, 116 S. Ct. 1589, 134 L. Ed. 2d 809 - all three should display.
    # Use citation_core_key so Wash. 2d / Wn.2d variants do not create duplicate display rows.
    bases_seen: set[str] = set()
    for cit in out:
        mk = _citation_display_merge_key(cit)
        if mk:
            bases_seen.add(mk)
    has_verified = any(
        cit.get("verified") is True or cit.get("verified") == "true" for cit in out
    )
    for mt in member_texts:
        base = extract_display_base_citation(mt)
        if not base:
            continue
        merge_k = citation_core_key(base)
        if not merge_k or merge_k in bases_seen:
            continue
        bases_seen.add(merge_k)
        parallel_cit = {
            "citation": mt,
            "text": mt,
            "display_base_citation": base,
            "true_by_parallel": has_verified,
        }
        out.append(parallel_cit)
    return out


def deduplicate_cluster_citations(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate display rows by citation_core_key (e.g. Wash. 2d vs Wn.2d merge to one line).

    Prefer verified over unverified. When verification ties, keep the first citation in list
    order so the reporter spelling matches the document's primary occurrence.
    """
    if not citations:
        return []
    if len(citations) <= 1:
        return list(citations)

    base_map: Dict[str, Dict[str, Any]] = {}
    unparseable: List[Dict[str, Any]] = []
    for c in citations:
        if not c:
            continue
        raw = (c.get("citation") or c.get("text") or "").strip()
        base = c.get("display_base_citation") or extract_display_base_citation(raw)
        merge_key = _citation_display_merge_key(c)
        if merge_key:
            existing = base_map.get(merge_key)
            cur_verified = c.get("verified") is True or c.get("verified") == "true"
            if existing is None:
                nc = dict(c)
                if base and not nc.get("display_base_citation"):
                    nc["display_base_citation"] = base
                base_map[merge_key] = nc
            else:
                existing_verified = existing.get("verified") is True or existing.get("verified") == "true"
                if cur_verified and not existing_verified:
                    nc = dict(c)
                    if base:
                        nc["display_base_citation"] = nc.get("display_base_citation") or base
                    base_map[merge_key] = nc
                # Same verification tier: keep existing (preserves document order / first spelling)
        else:
            key = raw.replace(" ", " ").strip()
            if key and not any(
                (u.get("citation") or u.get("text") or "").strip().replace(" ", " ") == key
                for u in unparseable
            ):
                unparseable.append(dict(c))
    return list(base_map.values()) + unparseable


def _citation_keys_for_cluster(cluster: Dict[str, Any]) -> set[str]:
    """Set of citation core keys for this cluster (ASCII-normalized for consistent matching)."""
    keys: set[str] = set()
    try:
        from src.utils.extraction_cleaner import normalize_to_ascii_display
    except Exception:
        normalize_to_ascii_display = lambda s: str(s or "")

    def _add_key(ct: str) -> None:
        if not ct:
            return
        s = normalize_to_ascii_display(str(ct))
        base = extract_display_base_citation(s) or s
        k = citation_core_key(base)
        if k:
            keys.add(k)
        # Fallback: use normalized raw string when core_key would be generic (catches Wn. App. etc.)
        fallback = re.sub(r"\s+", " ", base.strip()).lower()
        if fallback and len(fallback) > 5:
            keys.add(fallback)

    for c in cluster.get("citations") or cluster.get("citation_objects") or []:
        if isinstance(c, dict):
            _add_key(
                c.get("citation") or c.get("text") or c.get("citation_text") or c.get("display_base_citation") or ""
            )
        elif isinstance(c, str):
            _add_key(c)
    for m in cluster.get("cluster_members") or []:
        ct = m.get("citation", m) if isinstance(m, dict) else str(m)
        _add_key(ct)
    return keys


def _normalize_real_case_url(url: str) -> str:
    """Stable identity for a real case URL (not Google search). Drops query/fragment; lowercases host."""
    from urllib.parse import urlparse, urlunparse

    s = (url or "").strip()
    if not s:
        return ""
    p = urlparse(s)
    path = (p.path or "").rstrip("/")
    return urlunparse((p.scheme.lower(), (p.netloc or "").lower(), path, "", "", ""))


def merge_clusters_by_shared_real_canonical_url(clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge clusters that point at the same opinion URL (e.g. duplicate cards after parallel splits).

    Call after per-cluster display finalization when clusters may still share one CourtListener URL
    but different reporter strings. Uses :func:`get_canonical_url` so Google search fallbacks never merge.
    """
    if not clusters or len(clusters) <= 1:
        return clusters

    from collections import defaultdict

    from src.pipeline.clustering import merge_cluster_group
    from src.utils.cluster_display_utils import get_canonical_url

    url_to_indices: Dict[str, List[int]] = defaultdict(list)
    for i, cl in enumerate(clusters):
        if not isinstance(cl, dict):
            continue
        u = get_canonical_url(cl)
        if not u:
            continue
        url_to_indices[_normalize_real_case_url(u)].append(i)

    to_remove: set[int] = set()
    for _nu, idxs in url_to_indices.items():
        if len(idxs) <= 1:
            continue
        idxs = sorted(idxs)
        leader = idxs[0]
        merged = merge_cluster_group([clusters[j] for j in idxs])
        clusters[leader] = merged
        for j in idxs[1:]:
            to_remove.add(j)

    if not to_remove:
        return clusters
    return [c for i, c in enumerate(clusters) if i not in to_remove and isinstance(c, dict)]


def merge_clusters_by_shared_citation(clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge clusters that share any citation key, regardless of extracted name/year.
    Catches duplicates like "Erickson v. Pharmacia LLC, 2025" and "Kerry L. Erickson v. Pharmacia, 2024"
    when both cite 31 Wn. App. 2d 100 - same case, different extraction noise.
    """
    if not clusters or len(clusters) <= 1:
        return clusters
    from collections import defaultdict
    from src.pipeline.clustering import merge_cluster_group

    rows: List[Tuple[int, Dict[str, Any], set[str]]] = []
    for i, cl in enumerate(clusters):
        if not isinstance(cl, dict):
            continue
        keys = _citation_keys_for_cluster(cl)
        if not keys:
            continue
        rows.append((i, cl, keys))

    # Union-find: merge clusters that share ≥1 citation key
    parent: Dict[int, int] = {}

    def find(x: int) -> int:
        if x not in parent:
            parent[x] = x
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: int, b: int) -> None:
        parent[find(a)] = find(b)

    indices = [r[0] for r in rows]
    key_sets = {r[0]: r[2] for r in rows}

    # Same-case guard: extract best name per cluster for validation
    from src.utils.same_case import names_are_same_case, has_case_name
    def _best_cluster_name(cl: Dict[str, Any]) -> str:
        for field in ("canonical_name", "case_name", "extracted_case_name"):
            v = (cl.get(field) or "").strip()
            if v and v != "N/A":
                return v
        for cit in cl.get("citations") or []:
            if isinstance(cit, dict):
                for field in ("canonical_name", "extracted_case_name"):
                    v = (cit.get(field) or "").strip()
                    if v and v != "N/A":
                        return v
        return ""

    cluster_names = {r[0]: _best_cluster_name(r[1]) for r in rows}

    for ii, i in enumerate(indices):
        for j in indices[ii + 1 :]:
            if key_sets[i] & key_sets[j]:
                # Guard: don't merge clusters with clearly different case names
                ni, nj = cluster_names.get(i, ""), cluster_names.get(j, "")
                if has_case_name(ni) and has_case_name(nj) and not names_are_same_case(ni, nj):
                    logger.debug(
                        f"[SHARED-CIT-GUARD] Skipping merge: '{ni[:40]}' vs '{nj[:40]}' "
                        f"(shared keys: {key_sets[i] & key_sets[j]})"
                    )
                    continue
                union(i, j)

    components: Dict[int, List[int]] = defaultdict(list)
    for i in indices:
        components[find(i)].append(i)

    to_remove: set[int] = set()
    for _root, comp in components.items():
        if len(comp) <= 1:
            continue
        comp_clusters = [clusters[i] for i in comp]
        merged = merge_cluster_group(comp_clusters)
        for i in comp:
            if i != comp[0]:
                to_remove.add(i)
        clusters[comp[0]] = merged

    if not to_remove:
        return clusters
    return [c for i, c in enumerate(clusters) if i not in to_remove and isinstance(c, dict)]


def merge_clusters_by_scotus_parallel_reporters(
    clusters: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Merge clusters that are SCOTUS parallel cites (U.S. / S. Ct. / L. Ed.) for one case.

    ``merge_clusters_by_shared_citation`` does not apply: core keys differ
    (e.g. ``550 u.s. 544`` vs ``167 l. ed. 2d 929``).  This pass unions clusters
    that are *all* supreme-tier reporters, share the same decision year, and pass
    ``names_are_same_case`` (including defendant-only labels like ``Twombly``).
    """
    if not clusters or len(clusters) <= 1:
        return clusters

    from collections import defaultdict

    from src.pipeline.clustering import merge_cluster_group
    from src.utils.post_verify_split import reporter_tier
    from src.utils.same_case import has_case_name, names_are_same_case

    def _all_supreme(cl: Dict[str, Any]) -> bool:
        cits = cl.get("citations") or cl.get("citation_objects") or []
        if not cits:
            return False
        for c in cits:
            if not isinstance(c, dict):
                return False
            ct = (c.get("citation") or c.get("text") or c.get("citation_text") or "").strip()
            if not ct or reporter_tier(ct) != "supreme":
                return False
        return True

    def _parallel_year(cl: Dict[str, Any]) -> str:
        for fld in (
            "extracted_date",
            "cluster_year",
            "verifying_display_date",
            "canonical_date",
            "submitted_display_date",
        ):
            y = cl.get(fld)
            if y:
                m = re.search(r"(?:19|20)\d{2}", str(y))
                if m:
                    return m.group(0)
        for fld in ("extracted_case_name", "submitted_display_name", "cluster_case_name"):
            n = (cl.get(fld) or "").strip()
            if n:
                m = re.search(r"(?:19|20)\d{2}", n)
                if m:
                    return m.group(0)
        for cit in cl.get("citations") or []:
            if not isinstance(cit, dict):
                continue
            for fld in ("extracted_date", "canonical_date"):
                y = cit.get(fld)
                if y:
                    m = re.search(r"(?:19|20)\d{2}", str(y))
                    if m:
                        return m.group(0)
        return ""

    def _best_cluster_label(cl: Dict[str, Any]) -> str:
        for field in ("canonical_name", "extracted_case_name", "submitted_display_name", "cluster_case_name"):
            v = (cl.get(field) or "").strip()
            if v and v != "N/A":
                return v
        for cit in cl.get("citations") or []:
            if isinstance(cit, dict):
                for field in ("canonical_name", "extracted_case_name"):
                    v = (cit.get(field) or "").strip()
                    if v and v != "N/A":
                        return v
        return ""

    rows: List[Tuple[int, str, str]] = []
    for i, cl in enumerate(clusters):
        if not isinstance(cl, dict):
            continue
        if not _all_supreme(cl):
            continue
        yr = _parallel_year(cl)
        if not yr:
            continue
        nm = _best_cluster_label(cl)
        if not nm:
            continue
        rows.append((i, yr, nm))

    if len(rows) <= 1:
        return clusters

    parent: Dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: int, b: int) -> None:
        parent[find(a)] = find(b)

    for ii in range(len(rows)):
        i, yi, ni = rows[ii]
        for jj in range(ii + 1, len(rows)):
            j, yj, nj = rows[jj]
            if yi != yj:
                continue
            if not (has_case_name(ni) or has_case_name(nj)):
                continue
            if names_are_same_case(ni, nj):
                union(i, j)

    components: Dict[int, List[int]] = defaultdict(list)
    for i, _, _ in rows:
        components[find(i)].append(i)

    to_remove: set[int] = set()
    for _root, idxs in components.items():
        if len(idxs) <= 1:
            continue
        comp_clusters = [clusters[i] for i in idxs]
        merged = merge_cluster_group(comp_clusters)
        leader = idxs[0]
        clusters[leader] = merged
        for i in idxs[1:]:
            to_remove.add(i)

    if not to_remove:
        return clusters
    return [c for idx, c in enumerate(clusters) if idx not in to_remove and isinstance(c, dict)]


def promote_parallel_siblings_in_clusters(
    clusters: List[Dict[str, Any]],
    citations_list: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """Mark unverified citations as ``true_by_parallel`` when they share a cluster with a verified parallel cite.

    PARALLEL-CONSISTENCY (rq_worker) uses proximity / ``parallel_citations`` and strict same-name rules,
    and it runs *before* late cluster merges (e.g. :func:`merge_clusters_by_scotus_parallel_reporters`).
    After those merges, sibling reporters (U.S. / S. Ct. / L. Ed.) sit in one cluster but may still lack
    ``true_by_parallel``.  This pass fixes that so the UI shows "Verified by Parallel" per product rules.

    Returns the number of citations newly marked ``true_by_parallel``.
    """
    if not clusters:
        return 0

    from src.rq_worker_helpers import (
        _are_parallel_reporter_types,
        _citations_compatible_for_parallel,
    )
    from src.utils.post_verify_split import reporter_tier
    from src.utils.same_case import names_are_same_case

    def _real_case_url(c: Dict[str, Any]) -> bool:
        u = (c.get("canonical_url") or c.get("url") or "").strip()
        if not u:
            return False
        s = u.lower()
        return not (s.startswith("https://www.google.com/search") or s.startswith("http://www.google.com/search"))

    def _cit_label(c: Dict[str, Any]) -> str:
        return (c.get("canonical_name") or c.get("extracted_case_name") or "").strip()

    def _cit_year(c: Dict[str, Any]) -> Optional[str]:
        for fld in ("canonical_date", "extracted_date"):
            m = re.search(r"\b(19|20)\d{2}\b", str(c.get(fld) or ""))
            if m:
                return m.group(0)
        m = re.search(r"\b(19|20)\d{2}\b", str(c.get("citation") or ""))
        return m.group(0) if m else None

    promoted: Dict[str, Dict[str, Any]] = {}
    count = 0

    for cl in clusters:
        if not isinstance(cl, dict):
            continue
        cits = [c for c in (cl.get("citations") or cl.get("citation_objects") or []) if isinstance(c, dict)]
        if len(cits) < 2:
            continue
        sources = [c for c in cits if c.get("verified") is True and _real_case_url(c)]
        if not sources:
            continue
        cluster_fallback = (
            (cl.get("canonical_name") or cl.get("cluster_case_name") or cl.get("extracted_case_name") or "").strip()
        )
        for src in sources:
            src_txt = (src.get("citation") or src.get("text") or "").strip()
            if not src_txt:
                continue
            n_src = _cit_label(src) or cluster_fallback
            if not n_src:
                continue
            y_src = _cit_year(src)
            src_tier = reporter_tier(src_txt)
            for tgt in cits:
                if tgt is src:
                    continue
                if tgt.get("verified") is True:
                    continue
                if tgt.get("true_by_parallel") is True or tgt.get("true_by_parallel") == "true":
                    continue
                tgt_txt = (tgt.get("citation") or tgt.get("text") or "").strip()
                if not tgt_txt or tgt_txt == src_txt:
                    continue
                if not _are_parallel_reporter_types(src_txt, tgt_txt):
                    continue
                if not _citations_compatible_for_parallel(src_txt, tgt_txt):
                    continue
                tgt_tier = reporter_tier(tgt_txt)
                if src_tier in {"supreme", "district", "circuit"} and tgt_tier in {"supreme", "district", "circuit"}:
                    if src_tier != tgt_tier:
                        continue
                n_tgt = _cit_label(tgt) or cluster_fallback
                if not n_tgt:
                    continue
                if not names_are_same_case(n_src, n_tgt):
                    continue
                y_tgt = _cit_year(tgt)
                if y_src and y_tgt and y_src != y_tgt:
                    continue
                tgt["true_by_parallel"] = True
                tgt["verification_status"] = "verified_by_parallel"
                md_raw = tgt.get("metadata")
                md: Dict[str, Any] = dict(md_raw) if isinstance(md_raw, dict) else {}
                md["true_by_parallel"] = True
                tgt["metadata"] = md
                if src.get("canonical_name") and not tgt.get("canonical_name"):
                    tgt["canonical_name"] = src.get("canonical_name")
                if src.get("canonical_date") and not tgt.get("canonical_date"):
                    tgt["canonical_date"] = src.get("canonical_date")
                if src.get("canonical_url") and not tgt.get("canonical_url"):
                    tgt["canonical_url"] = src.get("canonical_url")
                if src.get("url") and not tgt.get("url"):
                    tgt["url"] = src.get("url")
                promoted[tgt_txt] = {
                    "true_by_parallel": True,
                    "verification_status": "verified_by_parallel",
                    "canonical_name": tgt.get("canonical_name"),
                    "canonical_date": tgt.get("canonical_date"),
                    "canonical_url": tgt.get("canonical_url"),
                    "url": tgt.get("url"),
                    "metadata": tgt.get("metadata"),
                }
                count += 1

    if citations_list and promoted:
        for c in citations_list:
            if not isinstance(c, dict):
                continue
            k = (c.get("citation") or c.get("text") or "").strip()
            if k in promoted:
                upd = promoted[k]
                for fld, val in upd.items():
                    if val is not None:
                        c[fld] = val

    return count


def merge_clusters_by_same_case_identity(clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge clusters that represent the same case: same normalized extracted name,
    same extracted year, and at least one citation in common. Prevents the same
    case from appearing in both Unverified and Possible Matches.
    """
    if not clusters or len(clusters) <= 1:
        return clusters

    try:
        from src.utils.clustering_utils import normalize_case_name_for_clustering
    except Exception:
        def normalize_case_name_for_clustering(case_name: Optional[str]) -> str:
            if not case_name or str(case_name).strip() in ("", "N/A", "Unknown"):
                return "unknown"
            return re.sub(r"\s+", "_", re.sub(r"[^\w\s]", "", str(case_name).lower().strip()))

    def get_year(cl: Dict[str, Any]) -> str:
        y = cl.get("extracted_date") or cl.get("cluster_year") or cl.get("submitted_display_date") or ""
        if not y:
            # Fallback: extract year from name so "Lindstrom 2025" and "Lindstrom" (with date elsewhere) can group
            name = (cl.get("extracted_case_name") or cl.get("submitted_display_name") or "").strip()
            if name:
                ym = re.search(r"(?:19|20)\d{2}", name)
                if ym:
                    return ym.group(0)
            return ""
        s = str(y).strip()
        m = re.search(r"(?:19|20)\d{2}", s)
        return m.group(0) if m else s[:4] if len(s) >= 4 else ""

    # Strip trailing year from name so "United States v. Lindstrom, 2025" and "United States v. Lindstrom" group together
    def _name_for_merge_group(name: str) -> str:
        if not name or name.strip() == "N/A":
            return ""
        s = re.sub(r",?\s*(?:19|20)\d{2}\s*$", "", str(name).strip()).strip()
        return normalize_case_name_for_clustering(s) if s else ""

    # (index, cluster, norm_name, year, keys)
    rows: List[Tuple[int, Dict[str, Any], str, str, set[str]]] = []
    for i, cl in enumerate(clusters):
        if not isinstance(cl, dict):
            continue
        name = (cl.get("extracted_case_name") or cl.get("submitted_display_name") or "").strip()
        norm_name = _name_for_merge_group(name) if name and name != "N/A" else ""
        year = get_year(cl)
        keys = _citation_keys_for_cluster(cl)
        if not norm_name and not keys:
            continue
        rows.append((i, cl, norm_name or "unknown", year, keys))

    # Group by (norm_name, year); within each group, merge clusters that share ≥1 citation key (transitive).
    from collections import defaultdict
    groups: Dict[Tuple[str, str], List[Tuple[int, Dict[str, Any], set[str]]]] = defaultdict(list)
    for i, cl, norm_name, year, keys in rows:
        groups[(norm_name, year)].append((i, cl, keys))

    to_remove: set[int] = set()
    for (_name, _year), group in groups.items():
        if len(group) <= 1:
            continue
        # Connected components: two clusters merge if they share at least one citation key.
        parent: Dict[int, int] = {}

        def find(x: int) -> int:
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(a: int, b: int) -> None:
            parent[find(a)] = find(b)

        indices = [g[0] for g in group]
        key_sets = {g[0]: g[2] for g in group}
        for ii, i in enumerate(indices):
            for j in indices[ii + 1 :]:
                if key_sets[i] & key_sets[j]:
                    union(i, j)

        components: Dict[int, List[int]] = defaultdict(list)
        for i in indices:
            components[find(i)].append(i)

        for _root, comp in components.items():
            if len(comp) <= 1:
                continue
            # Merge comp into leader (prefer verified, then most citations)
            comp_clusters = [(i, clusters[i]) for i in comp]
            leader_idx = comp[0]
            leader = clusters[leader_idx]
            for i in comp[1:]:
                other = clusters[i]
                l_verified = any(
                    isinstance(c, dict) and is_effectively_verified_citation(c)
                    for c in (leader.get("citations") or leader.get("citation_objects") or [])
                )
                o_verified = any(
                    isinstance(c, dict) and is_effectively_verified_citation(c)
                    for c in (other.get("citations") or other.get("citation_objects") or [])
                )
                l_size = len(leader.get("citations") or leader.get("citation_objects") or [])
                o_size = len(other.get("citations") or other.get("citation_objects") or [])
                if (o_verified and not l_verified) or (o_size > l_size and not (l_verified and not o_verified)):
                    leader_idx = i
                    leader = other
            # Merge all in comp into leader (leader_idx)
            leader = clusters[leader_idx]
            for i in comp:
                if i == leader_idx:
                    continue
                to_remove.add(i)
                other = clusters[i]
                for key in ("cluster_members", "citations"):
                    leader_list = list(leader.get(key) or [])
                    other_list = other.get(key) or []
                    if key == "cluster_members":
                        existing = {m.get("citation", "") if isinstance(m, dict) else str(m) for m in leader_list}
                    else:
                        existing = {c.get("citation", "") if isinstance(c, dict) else str(c) for c in leader_list}
                    for item in other_list:
                        ct = item.get("citation", "") if isinstance(item, dict) else str(item)
                        if ct and ct not in existing:
                            leader_list.append(item)
                            existing.add(ct)
                    leader[key] = leader_list
                leader["citation_objects"] = leader.get("citations") or []
                if not leader.get("extracted_date") and other.get("extracted_date"):
                    leader["extracted_date"] = other["extracted_date"]
                if not leader.get("cluster_year") and other.get("cluster_year"):
                    leader["cluster_year"] = other["cluster_year"]
                leader["cluster_size"] = len(leader.get("cluster_members", []))
                leader["size"] = len(leader.get("citations") or leader.get("citation_objects") or [])

    if not to_remove:
        return clusters
    return [c for i, c in enumerate(clusters) if i not in to_remove and isinstance(c, dict)]


def deduplicate_clusters_for_response(clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove structurally duplicate clusters using a stable identity key so repeated
    cards don't appear in UI (e.g., identical case/year with same citation set).
    """
    if not clusters:
        return []

    def _norm(v: Any) -> str:
        return re.sub(r"\s+", " ", str(v or "").strip().lower())

    def _cluster_key(cl: Dict[str, Any]) -> str:
        try:
            from src.utils.cluster_display_utils import get_canonical_url

            u = get_canonical_url(cl)
            if u:
                return f"url:{_normalize_real_case_url(u)}"
        except Exception:
            pass

        cits = cl.get("citations") or cl.get("citation_objects") or []
        keys: List[str] = []
        for c in cits:
            if not isinstance(c, dict):
                continue
            ct = c.get("citation") or c.get("text") or ""
            base = extract_display_base_citation(str(ct)) or str(ct)
            k = citation_core_key(base)
            if k:
                keys.append(k)
        # Use cluster_members when citations don't yield keys (avoids different keys for same case)
        if not keys and cl.get("cluster_members"):
            for m in cl.get("cluster_members") or []:
                ct = m.get("citation", m) if isinstance(m, dict) else str(m)
                if ct:
                    base = extract_display_base_citation(str(ct)) or str(ct)
                    k = citation_core_key(base)
                    if k:
                        keys.append(k)
        keys = sorted(set(keys))
        if keys:
            return f"citset:{'|'.join(keys)}"
        # Fallback when citations are malformed/empty.
        return (
            f"name:{_norm(cl.get('verifying_display_name') or cl.get('canonical_name') or cl.get('submitted_display_name'))}"
            f"|date:{_norm(cl.get('verifying_display_date') or cl.get('canonical_date') or cl.get('submitted_display_date'))}"
        )

    seen: Dict[str, Dict[str, Any]] = {}
    for cl in clusters:
        if not isinstance(cl, dict):
            continue
        key = _cluster_key(cl)
        if key in seen:
            # Prefer the cluster with more citations and effective verification signal.
            prev = seen[key]
            prev_cits = prev.get("citations") or prev.get("citation_objects") or []
            cur_cits = cl.get("citations") or cl.get("citation_objects") or []
            prev_has_verified = any(
                isinstance(c, dict) and is_effectively_verified_citation(c)
                for c in prev_cits
            )
            cur_has_verified = any(
                isinstance(c, dict) and is_effectively_verified_citation(c)
                for c in cur_cits
            )
            if (cur_has_verified and not prev_has_verified) or (len(cur_cits) > len(prev_cits)):
                seen[key] = cl
            continue
        seen[key] = cl
    # Rebuild using resolved winners while preserving original order.
    winners = set(id(v) for v in seen.values())
    return [cl for cl in clusters if isinstance(cl, dict) and id(cl) in winners]


def apply_proprietary_display_fallback(citations: List[Dict[str, Any]]) -> None:
    """
    Ensure unverified WL/LEXIS citations consistently expose proprietary reason.
    This is a display-level safety net for any late-path status drift.
    """
    if not citations:
        return
    msg = "Proprietary format - not available in free databases (Westlaw/Lexis only)"

    def _is_real_canonical_url(url_str: str) -> bool:
        """Return True only for real case URLs (CourtListener, etc.), not Google search fallbacks."""
        u = (url_str or "").strip()
        if not u or u.upper() == "N/A":
            return False
        if u.startswith("https://www.google.com/search?") or u.startswith("http://www.google.com/search?"):
            return False
        return True

    def _has_possible_match_evidence(c: Dict[str, Any]) -> bool:
        if not isinstance(c, dict):
            return False
        url = str(c.get("canonical_url") or c.get("url") or "").strip()
        md_raw = c.get("metadata")
        md: Dict[str, Any] = md_raw if isinstance(md_raw, dict) else {}
        pm_url = str(md.get("possible_match_url") or "").strip()
        # Possible-match requires a real case URL (CourtListener, etc.); Google search URLs do NOT qualify.
        return any(_is_real_canonical_url(v) for v in (url, pm_url))

    for c in citations:
        if not isinstance(c, dict):
            continue
        ct = str(c.get("citation") or c.get("text") or "")
        # Use citation-type flag when set (pipeline integration); else fall back to string check
        is_proprietary = c.get("is_proprietary_only") is True or is_proprietary_citation(ct)
        if not is_proprietary:
            continue
        if is_effectively_verified_citation(c):
            # Policy: proprietary citations without a direct URL should be
            # surfaced as "Verified by Parallel", not direct "Verified".
            # Do NOT set true_by_parallel when canonical_url is a Google search.
            direct_url = str(c.get("url") or "").strip()
            canonical_url = str(c.get("canonical_url") or "").strip()
            is_google = (
                (direct_url and not _is_real_canonical_url(direct_url))
                or (canonical_url and not _is_real_canonical_url(canonical_url))
            )
            if not direct_url and not is_google:
                c["verified"] = False
                c["is_verified"] = False
                c["true_by_parallel"] = True
                c["verification_status"] = "verified_by_parallel_not_in_document"
                md_raw = c.get("metadata")
                md: Dict[str, Any] = md_raw if isinstance(md_raw, dict) else {}
                md["true_by_parallel"] = True
                md["parallel_not_in_document"] = True
                c["metadata"] = md
            elif is_google:
                c["verified"] = False
                c["is_verified"] = False
                c["true_by_parallel"] = False
            continue
        c["verified"] = False
        c["is_verified"] = False
        is_possible = c.get("possible_match") is True or c.get("possible_match") == "true"
        if is_possible and not _has_possible_match_evidence(c):
            c["possible_match"] = False
            is_possible = False
        if is_possible:
            # Preserve possible_match_with_url so canonical link and name show (e.g. name+date-only fallback).
            current_status = (c.get("verification_status") or "").strip()
            if current_status != "possible_match_with_url":
                c["verification_status"] = current_status or "possible_match_gate_reject"
                if not c.get("error"):
                    c["error"] = "Possible match found but rejected by strict gate"
        else:
            c["verification_status"] = "proprietary_format"
            c["error"] = msg
            # Keep canonical fields empty for non-possible proprietary misses.
            c["canonical_url"] = None
            c["url"] = None
            c["canonical_name"] = None
            c["canonical_date"] = None


def compute_cluster_sections(clusters: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Categorize clusters into sections for the frontend. Returns cluster_id lists per section.
    Keys: unverified, case_mismatch, date_mismatch, verified_strict, other.
    (Verified-by-parallel citations appear in the same cluster as verified citations → verified_strict.)
    """
    sections: Dict[str, List[str]] = {
        "unverified": [],
        "case_mismatch": [],
        "date_mismatch": [],
        "verified_by_parallel": [],
        "verified_strict": [],
        "other": [],
    }

    def is_effectively_verified(cit: Dict[str, Any]) -> bool:
        if not cit:
            return False
        case_name = (cit.get("extracted_case_name") or cit.get("case_name") or "").strip().upper()
        if case_name == "N/A":
            partial_text = (cit.get("citation") or cit.get("text") or "").strip()
            if (
                re.search(r"\s_{2,}\s*(?:\(|$)", partial_text)
                or re.search(r"\s_{2,}\)", partial_text)
                or re.search(r"[.\s]_{2,}\s*$", partial_text)
            ):
                return False
        return is_effectively_verified_citation(cit)

    def is_effectively_verified_with_cluster(cit: Dict[str, Any], cluster: Dict[str, Any]) -> bool:
        if not cit:
            return False
        if not (cit.get("verified") is True or cit.get("verified") == "true" or cit.get("is_verified") is True):
            return False
        if has_canonical_url(cit):
            return True
        cu = (cluster.get("canonical_url") or cluster.get("display_canonical_url") or "").strip()
        return bool(cu)

    def _is_real_canonical_url(url_str: str) -> bool:
        """Return True only for real canonical URLs (not Google search fallbacks)."""
        u = (url_str or "").strip()
        if not u or u.upper() == "N/A":
            return False
        if u.startswith("https://www.google.com/search?") or u.startswith("http://www.google.com/search?"):
            return False
        return True

    def _cluster_has_real_url(cluster: Dict[str, Any], cits: List[Dict[str, Any]]) -> bool:
        """True if cluster or any citation has a real (non-Google) case URL. Used to separate Unverified (Google only) vs Possible Match (real URL)."""
        cu = (cluster.get("canonical_url") or cluster.get("display_canonical_url") or "").strip()
        if _is_real_canonical_url(cu):
            return True
        for c in cits or []:
            if not isinstance(c, dict):
                continue
            u = (c.get("canonical_url") or c.get("url") or "").strip()
            if _is_real_canonical_url(u):
                return True
            md = c.get("metadata") or {}
            pm = (md.get("possible_match_url") or "").strip()
            if _is_real_canonical_url(pm):
                return True
        return False

    def has_possible_match_evidence(cit: Dict[str, Any]) -> bool:
        if not cit:
            return False
        url = (cit.get("canonical_url") or cit.get("url") or "").strip()
        md_raw = cit.get("metadata")
        md: Dict[str, Any] = md_raw if isinstance(md_raw, dict) else {}
        pm_url = str(md.get("possible_match_url") or "").strip()
        # Keep sectioning strict: require a real (non-Google) canonical URL.
        return any(_is_real_canonical_url(v) for v in (url, pm_url))

    def has_date_mismatch_evidence(cit: Dict[str, Any]) -> bool:
        if not cit:
            return False
        canonical_url = str(cit.get("canonical_url") or cit.get("url") or "").strip()
        md_raw = cit.get("metadata")
        md: Dict[str, Any] = md_raw if isinstance(md_raw, dict) else {}
        pm_url = str(md.get("possible_match_url") or "").strip()
        # Require a real (non-Google) canonical URL to count as date mismatch evidence.
        # Without a real URL, the citation should be categorized as Unverified.
        return any(_is_real_canonical_url(v) for v in (canonical_url, pm_url))

    for cl in clusters:
        if not isinstance(cl, dict):
            continue
        cid = cl.get("cluster_id")
        if not cid:
            continue
        cits = cl.get("citations") or cl.get("citation_objects") or []
        if not isinstance(cits, list):
            continue

        # All clusters without any citation having a non-Google canonical URL → unverified
        if not _cluster_has_real_url(cl, cits):
            sections["unverified"].append(cid)
            continue

        verified_keys_in_cluster: set[str] = set()
        for _c in cits:
            if not isinstance(_c, dict):
                continue
            if not is_effectively_verified(_c):
                continue
            _ct = _c.get("citation") or _c.get("text") or ""
            _base = extract_display_base_citation(str(_ct)) or str(_ct)
            _k = citation_core_key(_base)
            if _k:
                verified_keys_in_cluster.add(_k)

        has_verified = any(is_effectively_verified(c) for c in cits if c)
        has_vbp = any(
            c and (c.get("true_by_parallel") is True or c.get("true_by_parallel") == "true")
            and _is_real_canonical_url(str(c.get("canonical_url") or c.get("url") or ""))
            for c in cits
        )
        has_unverified = any(
            c
            and not is_effectively_verified(c)
            and not (
                (c.get("true_by_parallel") is True or c.get("true_by_parallel") == "true")
                and _is_real_canonical_url(str(c.get("canonical_url") or c.get("url") or ""))
            )
            and not (
                (c.get("possible_match") is True or c.get("possible_match") == "true")
                and has_possible_match_evidence(c)
            )
            and not (
                isinstance(c, dict)
                and (
                    citation_core_key(
                        extract_display_base_citation(str(c.get("citation") or c.get("text") or ""))
                        or str(c.get("citation") or c.get("text") or "")
                    )
                    in verified_keys_in_cluster
                )
            )
            for c in cits
        )

        citation_has_name_mismatch = any(
            c and (c.get("name_mismatch") is True or c.get("name_mismatch") == "true")
            for c in cits
        )
        citation_has_date_mismatch = any(
            c
            and (
                c.get("date_mismatch") is True
                or c.get("date_mismatch") == "true"
                or str(c.get("verification_status") or "").strip().lower() == "year_mismatch"
            )
            and has_date_mismatch_evidence(c)
            for c in cits
        )
        no_name = not (bool(cl.get("has_name_mismatch")) or citation_has_name_mismatch)
        no_date = not (bool(cl.get("has_date_mismatch")) or citation_has_date_mismatch)

        # Case (name) mismatch (verified but name mismatch)
        if not no_name:
            sections["case_mismatch"].append(cid)
            continue
        # Date mismatch only
        if not no_date:
            sections["date_mismatch"].append(cid)
            continue
        # Verified by parallel: same cluster as verified citations; treat as verified (no separate section)
        if has_vbp and not has_verified:
            sections["verified_strict"].append(cid)
            continue
        # Unverified: no citation verified, has at least one unverified
        if not has_verified and has_unverified:
            sections["unverified"].append(cid)
            continue
        # Verified bucket: at least one verified citation and no mismatch. If any citation in the
        # cluster is verified (or verified-by-parallel), treat the whole cluster as verified section.
        if has_verified and no_name and no_date:
            sections["verified_strict"].append(cid)
            continue
        # Rule: Google Search URL (or no URL) → Unverified. Real case URL but not verified → Possible Match (other).
        if _cluster_has_real_url(cl, cits):
            sections["other"].append(cid)  # Possible Matches
        else:
            sections["unverified"].append(cid)  # Unverified (search the web link)

    # Conflict resolver: if the same citation key appears in both an unverified cluster
    # and a verified bucket cluster, prefer the verified bucket and remove from unverified.
    # (e.g. United States v. Lindstrom: WL-only cluster is dropped when a verified cluster exists.)
    def _citation_key(cit_text: str) -> str:
        s = str(cit_text or "")
        try:
            from src.utils.extraction_cleaner import normalize_to_ascii_display
            s = normalize_to_ascii_display(s)
        except Exception:
            pass
        base = extract_display_base_citation(s)
        return citation_core_key(base or s)

    cluster_by_id: Dict[str, Dict[str, Any]] = {
        str(cl.get("cluster_id")): cl
        for cl in clusters
        if isinstance(cl, dict) and cl.get("cluster_id")
    }

    def _keys_for_cluster(cluster_id: str) -> set[str]:
        cl = cluster_by_id.get(str(cluster_id))
        if not cl:
            return set()
        out: set[str] = set()
        for c in (cl.get("citations") or cl.get("citation_objects") or []):
            if not isinstance(c, dict):
                continue
            ct = c.get("citation") or c.get("text") or ""
            key = _citation_key(ct)
            if key:
                out.add(key)
        return out

    # Build keys cache once for all cluster IDs (avoids repeated work in resolvers and dedup).
    all_cids: set[str] = set()
    for section_list in sections.values():
        for e in section_list or []:
            if e is not None:
                all_cids.add(str(e))
    keys_by_cid: Dict[str, set[str]] = {cid: _keys_for_cluster(cid) for cid in all_cids}

    verified_cids = list(sections.get("verified_by_parallel", [])) + list(
        sections.get("verified_strict", [])
    )
    verified_keys: set[str] = set()
    for cid in verified_cids:
        verified_keys.update(keys_by_cid.get(str(cid), set()))

    if verified_keys and sections.get("unverified"):
        filtered_unverified: List[str] = []
        dropped = 0
        for cid in sections["unverified"]:
            keys = keys_by_cid.get(str(cid), set())
            if keys and (keys & verified_keys):
                dropped += 1
                continue
            filtered_unverified.append(cid)
        if dropped:
            sections["unverified"] = filtered_unverified

    # Intra-bucket resolver: avoid duplicate unverified entries for the same core citation key.
    if sections.get("unverified"):
        def _unverified_cluster_rank(cluster_id: str) -> Tuple[int, int, int]:
            cl = cluster_by_id.get(str(cluster_id)) or {}
            cits = cl.get("citations") or cl.get("citation_objects") or []
            if not isinstance(cits, list):
                cits = []

            has_canonical_without_url = False
            has_extracted_name = False
            for c in cits:
                if not isinstance(c, dict):
                    continue
                canonical_name = str(c.get("canonical_name") or "").strip()
                canonical_url = str(c.get("canonical_url") or c.get("url") or "").strip()
                extracted_name = str(c.get("extracted_case_name") or "").strip()
                if canonical_name and canonical_name.upper() != "N/A" and not canonical_url:
                    has_canonical_without_url = True
                if extracted_name and extracted_name.upper() != "N/A":
                    has_extracted_name = True

            return (
                0 if has_canonical_without_url else 1,
                1 if has_extracted_name else 0,
                len(cits),
            )

        unverified_raw = list(sections.get("unverified") or [])
        id_by_str: Dict[str, Any] = {str(cid): cid for cid in unverified_raw}
        unverified_cids = list(id_by_str.keys())
        rank_by_cid: Dict[str, Tuple[int, int, int]] = {
            cid: _unverified_cluster_rank(cid) for cid in unverified_cids
        }
        # Keep higher-ranked clusters first; drop later clusters that overlap keys with already kept clusters.
        ordered = sorted(
            unverified_cids,
            key=lambda cid: rank_by_cid.get(cid, (0, 0, 0)),
            reverse=True,
        )
        kept: List[str] = []
        seen_keys: set[str] = set()
        for cid in ordered:
            keys = keys_by_cid.get(cid) or set()
            if keys and (keys & seen_keys):
                continue
            kept.append(cid)
            seen_keys.update(keys)

        # Preserve original list order in output.
        chosen_cids = set(kept)
        deduped_unverified: List[str] = [cid for cid in unverified_cids if cid in chosen_cids]
        sections["unverified"] = [id_by_str.get(cid, cid) for cid in deduped_unverified]

    # Ensure no cluster appears in both unverified and other (Possible Matches).
    def _content_key_for_cluster(cluster_id: str) -> Optional[Tuple[str, str]]:
        """(normalized name, first citation key) for deduping same case across sections."""
        cl = cluster_by_id.get(str(cluster_id))
        if not cl:
            return None
        name = (cl.get("submitted_display_name") or cl.get("extracted_case_name") or "").strip()
        name = re.sub(r"\s+", " ", name).lower() if name else ""
        keys = keys_by_cid.get(str(cluster_id), set())
        first_key = next(iter(keys), None) if keys else None
        if not name and not first_key:
            return None
        return (name, first_key or "")

    # 1) Same cluster_id: remove from other if already in unverified.
    unverified_ids = {str(e) for e in (sections.get("unverified") or []) if e is not None}
    if unverified_ids:
        other_list = sections.get("other") or []
        sections["other"] = [e for e in other_list if str(e) not in unverified_ids]
    # 2) Same case (citation key overlap): remove from other if any citation key matches unverified.
    unverified_citation_keys = set()
    for cid in sections.get("unverified") or []:
        unverified_citation_keys.update(keys_by_cid.get(str(cid), set()))
    if unverified_citation_keys:
        other_list = sections.get("other") or []
        sections["other"] = [
            e for e in other_list
            if not (keys_by_cid.get(str(e), set()) & unverified_citation_keys)
        ]
    # 3) Same case (display identity): remove from other if (name, first citation) matches an unverified cluster.
    unverified_content_keys = set()
    for cid in sections.get("unverified") or []:
        k = _content_key_for_cluster(str(cid))
        if k:
            unverified_content_keys.add(k)
    if unverified_content_keys:
        other_list = sections.get("other") or []
        sections["other"] = [
            e for e in other_list
            if _content_key_for_cluster(str(e)) not in unverified_content_keys
        ]

    # 4) Same case (normalized name only): remove from other if display name matches any unverified cluster.
    # Handles duplicate clusters where citation keys or content keys differ (e.g. different citation text format).
    # Use canonical name form so "Door Props., LLC" and "Door Properties, LLC" match.
    def _normalize_display_name_for_dedup(name: str) -> str:
        if not name or not isinstance(name, str):
            return ""
        s = re.sub(r"\s+", " ", str(name).strip()).lower()
        s = re.sub(r",?\s*(?:19|20)\d{2}\s*$", "", s)  # strip trailing ", 2025" or " 2025"
        s = s.strip()
        # Canonicalize common legal abbreviations so "props." and "properties" match
        s = re.sub(r"\bprops\.?\b", "properties", s)
        s = re.sub(r"\bsec\.?\b", "sec", s)
        s = re.sub(r"\best\.?\b", "est", s)
        s = re.sub(r"\bcorp\.?\b", "corp", s)
        s = re.sub(r"\binc\.?\b", "inc", s)
        s = re.sub(r"\bllc\b", "llc", s)
        s = re.sub(r"\bltd\.?\b", "ltd", s)
        s = re.sub(r"\bco\.?\b", "co", s)
        s = re.sub(r"\bbros\.?\b", "bros", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    unverified_normalized_names: set[str] = set()
    for cid in sections.get("unverified") or []:
        cl = cluster_by_id.get(str(cid))
        if cl:
            n = _normalize_display_name_for_dedup(
                cl.get("submitted_display_name") or cl.get("extracted_case_name") or ""
            )
            if n:
                unverified_normalized_names.add(n)
    if unverified_normalized_names:
        other_list = sections.get("other") or []
        kept_other: List[str] = []
        for e in other_list:
            cl = cluster_by_id.get(str(e))
            name = (cl or {}).get("submitted_display_name") or (cl or {}).get("extracted_case_name") or ""
            if _normalize_display_name_for_dedup(name) not in unverified_normalized_names:
                kept_other.append(e)
        sections["other"] = kept_other

    return sections
