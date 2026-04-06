"""
Cluster building and merging for the unified pipeline.

Exposes: create_clusters_from_parallel_citations, split_clusters_by_canonical,
merge_clusters_by_canonical_name, merge_cluster_group, build_clusters.
"""

import re
import logging
from datetime import date
from typing import Any, Dict, List

from src.models import CitationResult
from src.pipeline.context import _is_generic_fallback_name, _is_statute_name
from src.utils.cluster_filter import filter_cluster_members_by_reporter
from src.utils.date_utils import extract_year_value, extract_year_from_citation
from src.utils.same_case import names_are_same_case

logger = logging.getLogger(__name__)


def merge_cluster_group(clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple clusters into a single cluster."""
    if not clusters:
        return {}
    if len(clusters) == 1:
        return clusters[0]

    verified_clusters = [c for c in clusters if c.get("verified", False)]
    base_cluster = verified_clusters[0] if verified_clusters else clusters[0]

    all_citations = []
    all_members = []
    for cluster in clusters:
        all_citations.extend(cluster.get("citations", []))
        all_members.extend(cluster.get("cluster_members", []))

    seen_members = set()
    unique_members = []
    for member in all_members:
        member_key = member.get("citation", "") if isinstance(member, dict) else member
        if member_key not in seen_members:
            seen_members.add(member_key)
            unique_members.append(member)

    seen_citations = set()
    unique_citations = []
    for cit in all_citations:
        if isinstance(cit, dict):
            cit_text = cit.get("citation", str(cit))
        else:
            cit_text = getattr(cit, "citation", str(cit))
        if cit_text not in seen_citations:
            seen_citations.add(cit_text)
            unique_citations.append(cit)

    merged = base_cluster.copy()
    merged["cluster_members"] = unique_members
    merged["citations"] = unique_citations
    merged["cluster_size"] = len(unique_citations)
    merged["merged_from"] = len(clusters)

    logger.info(
        f"[MERGE-CLUSTER] Merged {len(clusters)} clusters into 1 with {len(unique_citations)} citations"
    )
    return merged


def merge_clusters_by_canonical_name(
    clusters: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Merge clusters that have the same canonical_name or represent the same case.
    Also handles abbreviations like "TCAC" vs "Tri-Cities Animal Care & Control".
    """
    if not clusters or len(clusters) <= 1:
        return clusters

    def extract_first_party(name: str) -> str:
        if not name:
            return ""
        parts = re.split(r"\s+v\.?\s+", name, maxsplit=1, flags=re.IGNORECASE)
        return parts[0].lower().strip() if parts else name.lower().strip()

    def names_match(name1: str, name2: str) -> bool:
        if not name1 or not name2:
            return False
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        if n1 == n2:
            return True
        p1 = extract_first_party(name1)
        p2 = extract_first_party(name2)
        if p1 and p2:
            p1_words = set(re.findall(r"\b[a-z]+\b", p1))
            p2_words = set(re.findall(r"\b[a-z]+\b", p2))
            common = {"inc", "llc", "corp", "co", "the", "of", "and", "v"}
            p1_key = p1_words - common
            p2_key = p2_words - common
            if p1_key and p2_key and (p1_key & p2_key):
                return True
        return False

    for cluster in clusters:
        if not cluster.get("canonical_name") or cluster.get("canonical_name") == "N/A":
            for cit in cluster.get("citations", []):
                if isinstance(cit, dict):
                    cn = cit.get("canonical_name")
                    cu = cit.get("canonical_url")
                    verified = cit.get("verified", False)
                    cd = cit.get("canonical_date")
                else:
                    cn = getattr(cit, "canonical_name", None)
                    cu = getattr(cit, "canonical_url", None)
                    verified = getattr(cit, "verified", False)
                    cd = getattr(cit, "canonical_date", None)
                if cn and cn != "N/A" and verified:
                    cluster["canonical_name"] = cn
                    if cu:
                        cluster["canonical_url"] = cu
                    cluster["canonical_date"] = cd or cluster.get("canonical_date")
                    logger.info(
                        f"[MERGE-PROMOTE] Promoted canonical_name='{cn}' from citation to "
                        f"cluster_id={cluster.get('cluster_id')}"
                    )
                    break

    for cluster in clusters:
        cn = cluster.get("canonical_name")
        if not cn or cn == "N/A":
            cit_texts = []
            for cit in cluster.get("citations", [])[:3]:
                if isinstance(cit, dict):
                    cit_texts.append(cit.get("citation", "?")[:60])
                else:
                    cit_texts.append(getattr(cit, "citation", "?")[:60])
            logger.info(
                f"[MERGE-NO-CN] cluster_id={cluster.get('cluster_id')} has no canonical_name. "
                f"Citations: {cit_texts}"
            )

    def _merge_year_for_cluster(cluster: Dict[str, Any]) -> str:
        """Best-effort year for merge guards (prevents same-name cross-year merges)."""
        for field in (
            cluster.get("canonical_date"),
            cluster.get("cluster_year"),
            cluster.get("extracted_date"),
        ):
            y = extract_year_value(field)
            if y:
                return str(y)
        # Citation-level canonical_date (so same-case clusters with only citation-level date match).
        for cit in cluster.get("citations", []) or []:
            if isinstance(cit, dict):
                cd = cit.get("canonical_date") or cit.get("extracted_date")
            else:
                cd = getattr(cit, "canonical_date", None) or getattr(cit, "extracted_date", None)
            y = extract_year_value(cd)
            if y:
                return str(y)
        # Fall back to citation-intrinsic year (especially WL years).
        for cit in cluster.get("citations", []) or []:
            if isinstance(cit, dict):
                ctext = cit.get("citation") or cit.get("text") or ""
            else:
                ctext = getattr(cit, "citation", "") or ""
            y2 = extract_year_from_citation(str(ctext))
            if y2:
                return str(y2)
        return ""

    # Group clusters by same case (names_are_same_case) and year, so "Kustura v. Department..."
    # and "KUSTURA v. Dept. of Labor and Industries" merge — works for any legal doc.
    def _cluster_display_name(c: Dict[str, Any]) -> str:
        name = (
            (c.get("canonical_name") or "").strip()
            or (c.get("cluster_case_name") or "").strip()
            or (c.get("extracted_case_name") or "").strip()
        )
        if name and name != "N/A":
            return name
        # Fallback: first citation with canonical_name (so we can merge even when cluster-level not set)
        for cit in c.get("citations") or []:
            if isinstance(cit, dict):
                cn = (cit.get("canonical_name") or "").strip()
            else:
                cn = (getattr(cit, "canonical_name", None) or "").strip()
            if cn and cn != "N/A":
                return cn
        return ""

    name_to_clusters: List[List[Dict[str, Any]]] = []
    for cluster in clusters:
        canonical_name = _cluster_display_name(cluster)
        if not canonical_name or canonical_name == "N/A":
            continue
        year_key = (_merge_year_for_cluster(cluster) or "").strip() or "__unknown__"
        placed = False
        for bucket in name_to_clusters:
            b0_year = (_merge_year_for_cluster(bucket[0]) or "").strip() or "__unknown__"
            if b0_year != year_key:
                continue
            b0_name = _cluster_display_name(bucket[0])
            if names_are_same_case(canonical_name, b0_name):
                bucket.append(cluster)
                placed = True
                break
        if not placed:
            name_to_clusters.append([cluster])

    def _split_by_url(group: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        # Promote canonical_url from citations to cluster when missing (so same-case parallel cites merge)
        for c in group:
            if (c.get("canonical_url") or "").strip():
                continue
            for cit in c.get("citations") or []:
                if isinstance(cit, dict):
                    cu_val = cit.get("canonical_url")
                else:
                    cu_val = getattr(cit, "canonical_url", None)
                if cu_val:
                    c["canonical_url"] = (cu_val or "").strip()
                    break
        url_groups: List[List[Dict[str, Any]]] = []
        no_url: List[Dict[str, Any]] = []
        url_map: Dict[str, List[Dict[str, Any]]] = {}
        for c in group:
            cu = (c.get("canonical_url") or "").strip()
            if not cu:
                no_url.append(c)
            else:
                url_map.setdefault(cu, []).append(c)
        # Do NOT auto-attach no-url clusters to any URL group; that can merge
        # different cases that share a noisy canonical_name.
        if no_url:
            for c in no_url:
                url_groups.append([c])
        for members in url_map.values():
            url_groups.append(members)
        return url_groups

    merged_clusters = []
    # Clusters with no display name (cluster or from citations) pass through as-is
    for cluster in clusters:
        dn = _cluster_display_name(cluster)
        if not dn or dn == "N/A":
            merged_clusters.append(cluster)
    # Process each same-case+year bucket (grouped via names_are_same_case).
    # Merge entire bucket so parallel citations (same case, different reporters/URLs, e.g. Kustura
    # 169 Wn.2d vs 233 P.3d with different Court Listener IDs) become one cluster for any legal doc.
    _MAX_MERGE_YEAR_SPAN = 30

    def _split_bucket_by_extracted_year(bucket: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Guard: split a merge bucket when citations' extracted_dates span > _MAX_MERGE_YEAR_SPAN.
        Prevents re-merging clusters the master clustering correctly separated
        (e.g. '16 Wall. 36' ed=1873 with '7 Cranch 116' ed=1812)."""
        all_years: Dict[int, List[int]] = {}  # year -> list of bucket indices
        for idx, cluster in enumerate(bucket):
            for cit in cluster.get("citations", []) or []:
                ed = cit.get("extracted_date") if isinstance(cit, dict) else getattr(cit, "extracted_date", None)
                y = extract_year_value(ed)
                if y:
                    all_years.setdefault(int(y), []).append(idx)
        if not all_years:
            return [bucket]
        sorted_yrs = sorted(all_years.keys())
        if sorted_yrs[-1] - sorted_yrs[0] <= _MAX_MERGE_YEAR_SPAN:
            return [bucket]
        # Split by year gaps > _MAX_MERGE_YEAR_SPAN
        yr_to_bucket_id = {}
        bid = 0
        yr_to_bucket_id[sorted_yrs[0]] = bid
        for i in range(1, len(sorted_yrs)):
            if sorted_yrs[i] - sorted_yrs[i - 1] > _MAX_MERGE_YEAR_SPAN:
                bid += 1
            yr_to_bucket_id[sorted_yrs[i]] = bid
        # Assign clusters to sub-buckets based on majority year
        sub_buckets: Dict[int, List[Dict[str, Any]]] = {}
        for idx, cluster in enumerate(bucket):
            cit_years = []
            for cit in cluster.get("citations", []) or []:
                ed = cit.get("extracted_date") if isinstance(cit, dict) else getattr(cit, "extracted_date", None)
                y = extract_year_value(ed)
                if y:
                    cit_years.append(int(y))
            if cit_years:
                majority_yr = max(set(cit_years), key=cit_years.count)
                b = yr_to_bucket_id.get(majority_yr, 0)
            else:
                b = 0
            sub_buckets.setdefault(b, []).append(cluster)
        if len(sub_buckets) > 1:
            logger.info(
                f"[MERGE-YEAR-GUARD] Split merge bucket of {len(bucket)} clusters into "
                f"{len(sub_buckets)} sub-groups (year span {sorted_yrs[0]}-{sorted_yrs[-1]})"
            )
        return list(sub_buckets.values())

    for bucket in name_to_clusters:
        if len(bucket) > 1:
            sub_buckets = _split_bucket_by_extracted_year(bucket)
            for sub in sub_buckets:
                if len(sub) > 1:
                    logger.warning(
                        f"[MERGE-CLUSTERS] Merging {len(sub)} clusters for same case (year={_merge_year_for_cluster(sub[0])})"
                    )
                    merged_clusters.append(merge_cluster_group(sub))
                else:
                    merged_clusters.append(sub[0])
        else:
            merged_clusters.append(bucket[0])

    logger.info(
        f"[MERGE-CLUSTERS] After exact match: {len(clusters)} to {len(merged_clusters)} clusters"
    )

    if len(merged_clusters) > 1:
        date_party_groups: Dict[Any, List[int]] = {}
        for i, cluster in enumerate(merged_clusters):
            canonical_date = cluster.get("canonical_date") or ""
            canonical_name = cluster.get("canonical_name") or ""
            first_party = extract_first_party(canonical_name)
            if canonical_date and first_party and cluster.get("verified", False):
                key = (first_party, canonical_date)
                if key not in date_party_groups:
                    date_party_groups[key] = []
                date_party_groups[key].append(i)

        def _extracted_year_span(cluster_indices: List[int]) -> int:
            """Max extracted_date year span across all citations in the given cluster indices."""
            years = set()
            for idx in cluster_indices:
                for cit in merged_clusters[idx].get("citations", []) or []:
                    ed = cit.get("extracted_date") if isinstance(cit, dict) else getattr(cit, "extracted_date", None)
                    y = extract_year_value(ed)
                    if y:
                        years.add(int(y))
            return (max(years) - min(years)) if len(years) >= 2 else 0

        indices_to_merge = {}
        for key, indices in date_party_groups.items():
            if len(indices) > 1:
                if _extracted_year_span(indices) > _MAX_MERGE_YEAR_SPAN:
                    logger.info(
                        f"[MERGE-YEAR-GUARD] Skipping date+party merge for {key}: "
                        f"extracted_date year span > {_MAX_MERGE_YEAR_SPAN}"
                    )
                    continue
                leader = indices[0]
                for idx in indices[1:]:
                    indices_to_merge[idx] = leader
                    logger.info(
                        f"[MERGE-CLUSTERS] Will merge cluster {idx} into {leader} (same date+party: {key})"
                    )

        if indices_to_merge:
            leader_to_clusters: Dict[int, List[Dict[str, Any]]] = {}
            for i, cluster in enumerate(merged_clusters):
                leader = indices_to_merge.get(i, i)
                if leader not in leader_to_clusters:
                    leader_to_clusters[leader] = []
                leader_to_clusters[leader].append(cluster)

            final_merged = []
            processed = set()
            for i, cluster in enumerate(merged_clusters):
                leader = indices_to_merge.get(i, i)
                if leader in processed:
                    continue
                processed.add(leader)
                group = leader_to_clusters.get(leader, [cluster])
                if len(group) > 1:
                    final_merged.append(merge_cluster_group(group))
                else:
                    final_merged.append(cluster)
            merged_clusters = final_merged
            logger.info(
                f"[MERGE-CLUSTERS] After similarity pass: {len(merged_clusters)} clusters"
            )

    # Transitive parallel merge pass:
    # If same-case/same-year clusters have overlapping parallel citation universes,
    # merge connected components so A-B and B-C implies A-B-C.
    if len(merged_clusters) > 1:
        def _norm_case_for_transitive(cluster: Dict[str, Any]) -> str:
            name = (
                cluster.get("canonical_name")
                or cluster.get("cluster_case_name")
                or cluster.get("extracted_name")
                or ""
            )
            if not name:
                return ""
            return re.sub(r"\s+", " ", str(name).strip().lower())

        def _year_for_transitive(cluster: Dict[str, Any]) -> str:
            for field in (
                cluster.get("canonical_date"),
                cluster.get("cluster_year"),
                cluster.get("extracted_date"),
            ):
                m = re.search(r"(19|20)\d{2}", str(field or ""))
                if m:
                    return m.group(0)
            return ""

        def _parallel_universe(cluster: Dict[str, Any]) -> set[str]:
            universe: set[str] = set()
            for cit in cluster.get("citations", []) or []:
                if isinstance(cit, dict):
                    ctext = str(cit.get("citation", "") or "").strip()
                    if ctext:
                        universe.add(ctext)
                    for p in cit.get("parallel_citations", []) or []:
                        pt = str(p or "").strip()
                        if pt:
                            universe.add(pt)
                else:
                    ctext = str(getattr(cit, "citation", "") or "").strip()
                    if ctext:
                        universe.add(ctext)
                    for p in getattr(cit, "parallel_citations", []) or []:
                        pt = str(p or "").strip()
                        if pt:
                            universe.add(pt)
            for m in cluster.get("cluster_members", []) or []:
                if isinstance(m, dict):
                    mt = str(m.get("citation", "") or "").strip()
                else:
                    mt = str(m or "").strip()
                if mt:
                    universe.add(mt)
            return universe

        # Group candidate clusters by same normalized case+year first.
        by_sig: Dict[tuple[str, str], List[int]] = {}
        universes: Dict[int, set[str]] = {}
        for idx, cluster in enumerate(merged_clusters):
            c_name = _norm_case_for_transitive(cluster)
            c_year = _year_for_transitive(cluster)
            if not c_name or not c_year:
                continue
            sig = (c_name, c_year)
            by_sig.setdefault(sig, []).append(idx)
            universes[idx] = _parallel_universe(cluster)

        # For each signature bucket, merge connected components by overlap.
        if by_sig:
            merged_indices: set[int] = set()
            transitive_out: List[Dict[str, Any]] = []
            merged_components = 0
            for sig, idxs in by_sig.items():
                if len(idxs) < 2:
                    continue
                # Build overlap graph on indices.
                nbrs: Dict[int, set[int]] = {i: set() for i in idxs}
                for i, a in enumerate(idxs):
                    ua = universes.get(a, set())
                    if not ua:
                        continue
                    for b in idxs[i + 1 :]:
                        ub = universes.get(b, set())
                        if ub and (ua & ub):
                            nbrs[a].add(b)
                            nbrs[b].add(a)

                # Find connected components and merge those with >1 node.
                seen: set[int] = set()
                for start in idxs:
                    if start in seen:
                        continue
                    stack = [start]
                    comp: List[int] = []
                    seen.add(start)
                    while stack:
                        cur = stack.pop()
                        comp.append(cur)
                        for nxt in nbrs.get(cur, set()):
                            if nxt not in seen:
                                seen.add(nxt)
                                stack.append(nxt)
                    if len(comp) <= 1:
                        continue
                    merge_group = [merged_clusters[i] for i in sorted(comp)]
                    transitive_out.append(merge_cluster_group(merge_group))
                    merged_indices.update(comp)
                    merged_components += 1
                    logger.info(
                        f"[MERGE-CLUSTERS] Transitive parallel merge for case/year {sig}: "
                        f"{len(comp)} clusters -> 1"
                    )

            if merged_indices:
                # Keep untouched clusters + merged components.
                remainder = [
                    c for i, c in enumerate(merged_clusters) if i not in merged_indices
                ]
                merged_clusters = remainder + transitive_out
                logger.info(
                    f"[MERGE-CLUSTERS] After transitive pass: {len(merged_clusters)} clusters "
                    f"(merged components={merged_components})"
                )

    # Cross-cluster parallel merge: merge clusters whose citations explicitly
    # reference each other via parallel_citations, regardless of name or year.
    # This catches cases like Mountain Timber where the same case appears at
    # different court levels (state 1913, SCOTUS 1917) with reversed party order,
    # and Campbell & Gwinn where CourtListener returns a wrong canonical_name.
    if len(merged_clusters) > 1:
        # Build map: citation_text -> set of cluster indices that contain it
        cit_text_to_clusters: Dict[str, set] = {}
        for idx, cluster in enumerate(merged_clusters):
            for cit in cluster.get("citations", []) or []:
                if not isinstance(cit, dict):
                    continue
                ct = str(cit.get("citation", "") or "").strip()
                if ct:
                    cit_text_to_clusters.setdefault(ct, set()).add(idx)
                for m in cit.get("cluster_members", []) or []:
                    mt = str(m or "").strip()
                    if mt:
                        cit_text_to_clusters.setdefault(mt, set()).add(idx)

        # Build adjacency: cluster A links to cluster B if A's citation's
        # parallel_citations contains a citation text found in B
        cross_nbrs: Dict[int, set] = {i: set() for i in range(len(merged_clusters))}
        for idx, cluster in enumerate(merged_clusters):
            for cit in cluster.get("citations", []) or []:
                if not isinstance(cit, dict):
                    continue
                for p in cit.get("parallel_citations", []) or []:
                    pt = str(p or "").strip()
                    if not pt:
                        continue
                    for other_idx in cit_text_to_clusters.get(pt, set()):
                        if other_idx != idx:
                            cross_nbrs[idx].add(other_idx)
                            cross_nbrs[other_idx].add(idx)

        # Find connected components
        cross_seen: set = set()
        cross_merged_indices: set = set()
        cross_out: List[Dict[str, Any]] = []
        cross_count = 0
        for start_idx in range(len(merged_clusters)):
            if start_idx in cross_seen or not cross_nbrs.get(start_idx):
                continue
            stack = [start_idx]
            comp: List[int] = []
            cross_seen.add(start_idx)
            while stack:
                cur = stack.pop()
                comp.append(cur)
                for nxt in cross_nbrs.get(cur, set()):
                    if nxt not in cross_seen:
                        cross_seen.add(nxt)
                        stack.append(nxt)
            if len(comp) <= 1:
                continue
            merge_group = [merged_clusters[i] for i in sorted(comp)]
            cross_out.append(merge_cluster_group(merge_group))
            cross_merged_indices.update(comp)
            cross_count += 1
            names = [_cluster_display_name(merged_clusters[i])[:40] for i in sorted(comp)]
            logger.info(
                f"[MERGE-CLUSTERS] Cross-cluster parallel merge: {len(comp)} clusters -> 1 "
                f"(names: {names})"
            )

        if cross_merged_indices:
            remainder = [
                c for i, c in enumerate(merged_clusters) if i not in cross_merged_indices
            ]
            merged_clusters = remainder + cross_out
            logger.info(
                f"[MERGE-CLUSTERS] After cross-cluster parallel pass: {len(merged_clusters)} clusters "
                f"(merged {cross_count} groups)"
            )

    logger.info(
        f"[MERGE-CLUSTERS] Final: reduced from {len(clusters)} to {len(merged_clusters)} clusters"
    )
    return merged_clusters


def split_clusters_by_year(
    clusters: List[Dict[str, Any]],
    max_year_span: int = 30,
) -> List[Dict[str, Any]]:
    """
    Split any cluster whose citations' extracted_dates span > max_year_span.
    Parallel citations for the same case are always from the same year, so a wide
    span indicates cross-clustering (e.g. '16 Wall. 36' ed=1873 grouped with
    '7 Cranch 116' ed=1812 because both got ecn='Schooner Exchange').
    """
    if not clusters:
        return clusters
    result: List[Dict[str, Any]] = []
    split_count = 0
    for cluster in clusters:
        citations = cluster.get("citations") or []
        if len(citations) <= 1:
            result.append(cluster)
            continue
        # Collect extracted years
        cit_year_pairs = []
        for cit in citations:
            ed = cit.get("extracted_date") if isinstance(cit, dict) else getattr(cit, "extracted_date", None)
            y = extract_year_value(ed)
            cit_year_pairs.append((int(y) if y else None, cit))
        years = {y for y, _ in cit_year_pairs if y}
        if len(years) <= 1:
            result.append(cluster)
            continue
        sorted_yrs = sorted(years)
        if sorted_yrs[-1] - sorted_yrs[0] <= max_year_span:
            result.append(cluster)
            continue
        # Year span too large: split into sub-clusters by year buckets
        yr_to_bid = {}
        bid = 0
        yr_to_bid[sorted_yrs[0]] = bid
        for i in range(1, len(sorted_yrs)):
            if sorted_yrs[i] - sorted_yrs[i - 1] > max_year_span:
                bid += 1
            yr_to_bid[sorted_yrs[i]] = bid
        buckets: Dict[int, List[Any]] = {}
        no_year: List[Any] = []
        for y, cit in cit_year_pairs:
            if y is None:
                no_year.append(cit)
            else:
                b = yr_to_bid[y]
                buckets.setdefault(b, []).append(cit)
        # Assign no-year citations to the largest bucket
        if no_year and buckets:
            largest = max(buckets, key=lambda k: len(buckets[k]))
            buckets[largest].extend(no_year)
        elif no_year:
            buckets[0] = no_year
        if len(buckets) > 1:
            split_count += 1
            cit_texts = [
                (c.get("citation", "") if isinstance(c, dict) else getattr(c, "citation", ""))[:30]
                for c in citations
            ]
            logger.info(
                f"[SPLIT-CLUSTER-YEAR] Splitting cluster '{cluster.get('submitted_display_name', '')[:40]}' "
                f"into {len(buckets)} sub-clusters (year span {sorted_yrs[0]}-{sorted_yrs[-1]}): "
                f"{cit_texts[:4]}"
            )
            for b_cits in buckets.values():
                new_cluster = cluster.copy()
                new_cluster["citations"] = b_cits
                new_cluster["cluster_size"] = len(b_cits)
                new_cluster.pop("cluster_id", None)  # Force new ID assignment
                result.append(new_cluster)
        else:
            result.append(cluster)
    if split_count:
        logger.info(f"[SPLIT-CLUSTER-YEAR] Split {split_count} clusters by year, total now {len(result)}")
    return result


def split_clusters_by_canonical(
    clusters: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Split any cluster that contains citations from different canonical cases
    (different canonical_name and/or year). Also detect when citation text
    contains a different case name than canonical_name metadata.
    """
    if not clusters:
        return clusters
    result: List[Dict[str, Any]] = []

    def _norm_name(name: str) -> str:
        if not name:
            return ""
        n = re.sub(r"^See,?\s+e\.?g\.?,?\s*", "", str(name), flags=re.IGNORECASE)
        n = re.sub(r"^See\s+also\s+", "", n, flags=re.IGNORECASE)
        n = re.sub(r"^See\s+generally\s+", "", n, flags=re.IGNORECASE)
        n = re.sub(r"^But\s+see\s+", "", n, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", n).strip().lower()

    def _extract_first_party_from_text(cit_text: str) -> str:
        if not cit_text:
            return ""
        m = re.match(
            r"^([A-Z][A-Za-z'\-]+(?:\.\s*)?(?:\s+[A-Za-z'\-]+\.?)*)\s+v\.\s+",
            cit_text,
        )
        return m.group(1).strip().rstrip(",. ").split()[-1].lower() if m else ""

    def _year_from_any(value: str) -> int:
        m = re.search(r"(19|20)\d{2}", str(value or ""))
        return int(m.group(0)) if m else 0

    for cluster in clusters:
        citations = cluster.get("citations") or cluster.get("citation_objects") or []
        if len(citations) <= 1:
            result.append(cluster)
            continue
        canonical_groups: Dict[Any, List[Any]] = {}
        unassigned: List[Any] = []
        for cit in citations:
            if isinstance(cit, dict):
                can_name = cit.get("canonical_name")
                can_date = cit.get("canonical_date")
                can_url = cit.get("canonical_url") or cit.get("url")
                is_verified = cit.get("verified", False) or cit.get("is_verified", False)
                cit_text = cit.get("citation", "")
            else:
                can_name = getattr(cit, "canonical_name", None)
                can_date = getattr(cit, "canonical_date", None)
                can_url = getattr(cit, "canonical_url", None) or getattr(cit, "url", None)
                is_verified = getattr(cit, "verified", False)
                cit_text = getattr(cit, "citation", "")

            cit_text_party = _extract_first_party_from_text(cit_text)
            if cit_text_party and can_name and " v. " in can_name.lower():
                can_party = (
                    _norm_name(can_name).split(" v. ")[0].strip().split()[-1]
                    if " v. " in _norm_name(can_name)
                    else ""
                )
                # If canonical URL is present, trust URL identity over party-label differences.
                # This keeps true same-opinion parallels together even when captions differ.
                if can_party and cit_text_party != can_party and not can_url:
                    text_name_m = re.match(
                        r"^((?:[A-Z][A-Za-z'\-]+\.?(?:\s+[A-Za-z'\-]+\.?)*)"
                        r"\s+v\.\s+"
                        r"(?:[A-Z][A-Za-z'\-]+\.?(?:[\s,]+[A-Za-z'\-]+\.?)*))",
                        cit_text,
                    )
                    if text_name_m:
                        text_name = _norm_name(text_name_m.group(1).rstrip(","))
                        year_m = re.search(
                            r"\((?:[A-Za-z0-9.\s]*?)(\d{4})\)", cit_text
                        )
                        year_int = int(year_m.group(1)) if year_m else 0
                        key = (text_name, year_int)
                        canonical_groups.setdefault(key, []).append(cit)
                        logger.info(
                            f"[PIPELINE-CANONICAL-SPLIT] Citation text '{cit_text[:60]}' has different name "
                            f"than canonical '{can_name}' - grouping by text name '{text_name}'"
                        )
                        continue

            if is_verified and can_name and can_date:
                year_m = re.search(r"(19|20)\d{2}", str(can_date))
                year_int = int(year_m.group(0)) if year_m else 0
                if can_name:
                    # Group by same case (names_are_same_case) so "Kustura v. Department..."
                    # and "KUSTURA v. Dept. of Labor and Industries" stay together.
                    placed = False
                    for key_rep, group_cits in list(canonical_groups.items()):
                        if isinstance(key_rep, tuple) and len(key_rep) >= 1:
                            existing_name = key_rep[0]
                            existing_year = key_rep[1] if len(key_rep) > 1 else 0
                            if names_are_same_case(can_name, existing_name) and (year_int == 0 or existing_year == 0 or year_int == existing_year):
                                group_cits.append(cit)
                                placed = True
                                break
                    if not placed:
                        canonical_groups[(can_name, year_int)] = [cit]
                else:
                    unassigned.append(cit)
            else:
                unassigned.append(cit)

        if unassigned:
            logger.warning(
                f"[PIPELINE-CANONICAL-SPLIT] {len(unassigned)} unassigned citations in cluster "
                f"'{cluster.get('cluster_id', '?')}' with {len(canonical_groups)} canonical groups. "
                f"Unassigned ecns: {[((c.get('extracted_case_name') or '')[:40] if isinstance(c, dict) else (getattr(c, 'extracted_case_name', '') or '')[:40]) for c in unassigned]}"
            )
        if unassigned:
            for ua_cit in unassigned:
                if isinstance(ua_cit, dict):
                    ua_ecn = ua_cit.get("extracted_case_name") or ""
                    ua_date_str = str(
                        ua_cit.get("extracted_date", "")
                        or ua_cit.get("canonical_date", "")
                        or ""
                    )
                else:
                    ua_ecn = getattr(ua_cit, "extracted_case_name", "") or ""
                    ua_date_str = str(
                        getattr(ua_cit, "extracted_date", "")
                        or getattr(ua_cit, "canonical_date", "")
                        or ""
                    )
                ua_ecn_norm = (
                    _norm_name(ua_ecn)
                    if ua_ecn and ua_ecn != "N/A" and " v. " in ua_ecn
                    else ""
                )
                ua_cit_text = (
                    ua_cit.get("citation", "")
                    if isinstance(ua_cit, dict)
                    else (getattr(ua_cit, "citation", "") or "")
                )
                ua_year = _year_from_any(ua_date_str) or int(extract_year_from_citation(str(ua_cit_text)) or 0)
                assigned = False
                if ua_ecn_norm:
                    ua_parts = ua_ecn_norm.split(" v. ")
                    ua_first = (
                        ua_parts[0].strip().split()[-1] if ua_parts else ""
                    )
                    for key in list(canonical_groups.keys()):
                        key_parts = (
                            key[0].split(" v. ") if " v. " in key[0] else [key[0]]
                        )
                        key_first = (
                            key_parts[0].strip().split()[-1] if key_parts else ""
                        )
                        key_year = int(key[1]) if len(key) > 1 and isinstance(key[1], int) else _year_from_any(key[1] if len(key) > 1 else 0)
                        if (
                            ua_first
                            and key_first
                            and ua_first == key_first
                            and (ua_year == 0 or key_year == 0 or ua_year == key_year)
                        ):
                            canonical_groups[key].append(ua_cit)
                            assigned = True
                            break
                    if not assigned:
                        new_key = (ua_ecn_norm, ua_year)
                        canonical_groups.setdefault(new_key, []).append(ua_cit)
                        assigned = True
                        logger.info(
                            f"[PIPELINE-CANONICAL-SPLIT] Unassigned citation with ecn='{ua_ecn}' "
                            f"created new group '{new_key}' instead of dumping into primary"
                        )
                if not assigned:
                    # Never dump unassigned cites into the first canonical group.
                    # That behavior can mix different cases/years (e.g., Gomes 2020 vs 2021).
                    fallback_name = _norm_name(ua_ecn) if ua_ecn and ua_ecn != "N/A" else ""
                    if not fallback_name:
                        text_party = _extract_first_party_from_text(str(ua_cit_text))
                        fallback_name = f"textparty:{text_party}" if text_party else f"citation:{str(ua_cit_text).strip().lower()[:80]}"
                    new_key = (fallback_name, ua_year)
                    canonical_groups.setdefault(new_key, []).append(ua_cit)
                    logger.info(
                        f"[PIPELINE-CANONICAL-SPLIT] Forced standalone group for unassigned citation "
                        f"(ecn='{ua_ecn}', year={ua_year}, key='{new_key[0]}')"
                    )

        if len(canonical_groups) <= 1:
            result.append(cluster)
            continue

        def _best_year_from_cits(cits: List[Any]) -> int:
            """Prefer year from citation with highest reporter volume (e.g. 100 N.Y.2d over 86)."""
            best_year, best_vol = 0, 0
            for c in cits:
                ct = c.get("citation", "") if isinstance(c, dict) else getattr(c, "citation", "")
                y = _year_from_any(
                    c.get("canonical_date") or c.get("extracted_date") if isinstance(c, dict)
                    else getattr(c, "canonical_date", None) or getattr(c, "extracted_date", None)
                ) or int(extract_year_from_citation(str(ct)) or 0)
                m = re.search(r"(\d+)\s+(?:N\.?Y\.?2d|N\.?Y\.?3d)\s+\d+", ct, re.IGNORECASE)
                vol = int(m.group(1)) if m else 0
                if y and (vol > best_vol or (vol == best_vol and y > best_year)):
                    best_year, best_vol = y, vol
            if best_year:
                return best_year
            for c in cits:
                y = _year_from_any(
                    c.get("canonical_date") or c.get("extracted_date") if isinstance(c, dict)
                    else getattr(c, "canonical_date", None) or getattr(c, "extracted_date", None)
                )
                if y:
                    return y
            return 0

        # Merge groups that are the same case (keys may be (norm,) or (norm, year))
        merged_groups: Dict[Any, List[Any]] = {}
        for key in list(canonical_groups.keys()):
            norm_name = key[0]
            year_int = key[1] if len(key) > 1 else _best_year_from_cits(canonical_groups[key])
            merged_into = None
            for existing_key in list(merged_groups.keys()):
                if names_are_same_case(norm_name, existing_key[0]):
                    merged_into = existing_key
                    break
            if merged_into is not None:
                merged_groups[merged_into].extend(canonical_groups[key])
                # Use max year when same case has multiple decisions
                exist_year = existing_key[1] if len(existing_key) > 1 else _best_year_from_cits(merged_groups[merged_into])
                new_year = max(exist_year, year_int)
                if len(existing_key) > 1 and new_year != existing_key[1]:
                    cits = merged_groups.pop(merged_into)
                    merged_groups[(existing_key[0], new_year)] = cits
            else:
                merged_groups.setdefault(key, []).extend(canonical_groups[key])
        canonical_groups = merged_groups

        keys = sorted(canonical_groups.keys(), key=lambda k: (k[0], k[1] if len(k) > 1 else 0))
        logger.info(
            f"[PIPELINE-CANONICAL-SPLIT] Splitting cluster with mixed cases {[(k[0], k[1] if len(k) > 1 else '?') for k in keys]} into {len(keys)} clusters"
        )
        base_id = cluster.get("cluster_id", "cluster_0")
        for ki, key in enumerate(keys):
            norm_name = key[0]
            year_int = key[1] if len(key) > 1 else _best_year_from_cits(canonical_groups[key])
            group_cits = canonical_groups[key]
            group_cit_texts = {
                (
                    c.get("citation", "")
                    if isinstance(c, dict)
                    else getattr(c, "citation", "")
                )
                for c in group_cits
            }
            new_cluster = dict(cluster)
            new_cluster["cluster_id"] = (
                f"{base_id}_canonical_split_{ki}" if len(keys) > 1 else base_id
            )
            new_cits = [
                c
                for c in (cluster.get("citations") or [])
                if (
                    c.get("citation", "")
                    if isinstance(c, dict)
                    else getattr(c, "citation", "")
                )
                in group_cit_texts
            ]
            new_members = [
                m
                for m in (cluster.get("cluster_members") or [])
                if (
                    m.get("citation", "") if isinstance(m, dict) else m
                )
                in group_cit_texts
            ]
            new_cluster["citations"] = new_cits or group_cits
            new_cluster["cluster_members"] = new_members
            new_cluster["cluster_size"] = len(new_cluster["citations"])
            new_cluster["cluster_year"] = str(year_int)
            group_first = (
                norm_name.split(" v. ")[0].strip().split()[-1].lower()
                if " v. " in norm_name
                else norm_name.lower()
            )
            display_name = None
            for c in group_cits:
                cn = (
                    c.get("canonical_name", "")
                    if isinstance(c, dict)
                    else (getattr(c, "canonical_name", "") or "")
                )
                if not cn:
                    continue
                cn_norm = _norm_name(cn)
                cn_first = (
                    cn_norm.split(" v. ")[0].strip().split()[-1].lower()
                    if " v. " in cn_norm
                    else cn_norm.lower()
                )
                if cn_first == group_first:
                    display_name = cn
                    break

            def _cit_get(c, key):
                return (
                    c.get(key) if isinstance(c, dict) else getattr(c, key, None)
                )

            def _get_ecn(c):
                return (
                    c.get("extracted_case_name", "")
                    if isinstance(c, dict)
                    else (getattr(c, "extracted_case_name", "") or "")
                )

            ext_name_for_display = next(
                (
                    _get_ecn(c)
                    for c in group_cits
                    if _get_ecn(c) and _get_ecn(c) != "N/A"
                ),
                None,
            )
            new_cluster["cluster_case_name"] = (
                display_name
                or ext_name_for_display
                or cluster.get("cluster_case_name")
            )
            new_cluster["canonical_name"] = display_name or ""
            if not display_name:
                # PRESERVE URL: Only clear if there's no URL already
                # This prevents real canonical URLs from being lost during split
                existing_url = new_cluster.get("canonical_url") or next(
                    (_cit_get(c, "canonical_url") for c in group_cits if _cit_get(c, "canonical_url")),
                    None
                )
                if not existing_url:
                    new_cluster["canonical_url"] = None
                    new_cluster["canonical_date"] = None
                    new_cluster["verified"] = False
                    new_cluster["verification_status"] = None
                else:
                    # Keep the URL but mark as possible_match if not display_name
                    new_cluster["canonical_url"] = existing_url
                    new_cluster["possible_match"] = True
                    new_cluster["verification_status"] = "possible_match_split"
                    logger.info(
                        f"[PIPELINE-CANONICAL-SPLIT] Preserved URL for split cluster "
                        f"'{new_cluster['cluster_id']}' (URL present but no display_name)."
                    )
                if ext_name_for_display:
                    new_cluster["cluster_key"] = ext_name_for_display.lower()
                if not existing_url:
                    logger.warning(
                        f"[PIPELINE-CANONICAL-SPLIT] Cleared inherited canonical data for split cluster "
                        f"'{new_cluster['cluster_id']}' (no verified canonical_name in group). "
                        f"Using ecn='{ext_name_for_display}' for display."
                    )

            new_cluster["canonical_date"] = new_cluster.get(
                "canonical_date"
            ) or next(
                (
                    _cit_get(c, "canonical_date")
                    for c in group_cits
                    if _cit_get(c, "canonical_date")
                ),
                cluster.get("canonical_date"),
            )
            ext_name = next(
                (
                    _cit_get(c, "extracted_case_name")
                    for c in group_cits
                    if _cit_get(c, "extracted_case_name")
                ),
                None,
            )
            new_cluster["extracted_name"] = ext_name or cluster.get(
                "extracted_name"
            )
            new_cluster["extracted_date"] = next(
                (
                    _cit_get(c, "extracted_date")
                    for c in group_cits
                    if _cit_get(c, "extracted_date")
                ),
                cluster.get("extracted_date"),
            )
            result.append(new_cluster)
    return result


def build_clusters(
    citations: List[CitationResult],
) -> tuple[list[list[str]], dict[str, int]]:
    """Build clusters from parallel links and proximity; include singletons."""
    adj: dict[str, set[str]] = {}

    def add_edge(a: str, b: str) -> None:
        if not a or not b or a == b:
            return
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)

    for c in citations:
        adj.setdefault(c.citation, set())
    citation_set = {c.citation for c in citations}
    for c in citations:
        for p in c.parallel_citations or []:
            if p in citation_set:
                add_edge(c.citation, p)

    visited: set[str] = set()
    clusters: list[list[str]] = []
    citation_to_cluster: dict[str, int] = {}
    for node in adj.keys():
        if node in visited:
            continue
        stack = [node]
        comp: list[str] = []
        visited.add(node)
        while stack:
            v = stack.pop()
            comp.append(v)
            for w in adj.get(v, ()):
                if w not in visited:
                    visited.add(w)
                    stack.append(w)
        comp_sorted = sorted(comp)
        idx = len(clusters)
        clusters.append(comp_sorted)
        for cit in comp_sorted:
            citation_to_cluster[cit] = idx
    return clusters, citation_to_cluster
