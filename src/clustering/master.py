"""
Unified Clustering Master (Refactored)
========================================

This is a refactored version that delegates to the modular clustering package.
Maintains backward compatibility while using the new modular implementation.
"""

import re
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

# Import modular clustering components
from . import detection, propagation, validation, utils
from .detection import _clean_ecn, _get_segment_id, _same_case_check

logger = logging.getLogger(__name__)



class ClusterType(Enum):
    """Types of citation clusters."""
    PARALLEL = "parallel"
    CANONICAL = "canonical"
    EXTRACTED = "extracted"
    MIXED = "mixed"


@dataclass
class ClusterResult:
    """Standardized result from clustering."""
    cluster_id: str
    cluster_type: ClusterType
    case_name: Optional[str] = None
    case_year: Optional[str] = None
    citations: List[Any] = None
    size: int = 0
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    verification_status: Optional[str] = None


class UnifiedClusteringMaster:
    """
    THE SINGLE, AUTHORITATIVE clustering implementation (MODULAR VERSION).
    
    This refactored class uses the modular clustering package:
    - detection: Parallel and structural group detection
    - propagation: Metadata propagation within clusters
    - validation: Cluster quality validation
    - utils: Utility functions
    
    Maintains full backward compatibility with the original implementation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the master clustering engine."""
        self.config = config or {}
        self.debug_mode = self.config.get("debug_mode", False)
        self.min_cluster_size = self.config.get("min_cluster_size", 1)
        self.case_name_similarity_threshold = self.config.get(
            "case_name_similarity_threshold", 0.95
        )
        self.proximity_threshold = self.config.get("proximity_threshold", 150)
        self.enable_verification = self.config.get("enable_verification", True)

        logger.info("UnifiedClusteringMaster initialized - modular version")

    def cluster_citations(
        self, 
        citations: List[Any], 
        original_text: str = "", 
        enable_verification: bool = None,
        request_id: str = "",
        progress_callback: Optional[Callable[[int, str, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Main clustering method using modular components.
        
        Args:
            citations: List of citations to cluster
            original_text: Original document text
            enable_verification: Whether to enable verification
            request_id: Optional request ID for tracking
            progress_callback: Optional progress callback
            
        Returns:
            List of cluster dictionaries
        """
        if not citations:
            return []
        
        if enable_verification is None:
            enable_verification = self.enable_verification
        
        logger.info(f"[CLUSTERING] Starting modular clustering of {len(citations)} citations")
        
        # Step 1: Detect parallel groups using modular detection
        parallel_groups = detection.detect_parallel_groups(
            citations, 
            proximity_threshold=self.proximity_threshold,
            original_text=original_text
        )
        
        # Step 2: Detect structural groups
        structural_groups = detection.detect_structural_groups(
            citations, 
            original_text
        ) if original_text else []
        
        # Step 3: Merge groups
        all_groups = self._merge_groups(parallel_groups, structural_groups)
        
        # Step 3.25: Transitive merge — same case cited as A&B here and B&C later => one cluster
        # (Parallel citations = one case in multiple reporters; rare: A&B and B&C => A,B,C together.)
        all_groups = self._merge_groups_transitive(all_groups)
        
        # Step 3.5: Split groups by extracted_case_name
        # Proximity grouping may combine different cases cited near each other
        # (e.g., "Larimore v. Blaylock, 259 Va. 568 ... Swindle v. State, 10 Tenn. 581")
        all_groups = self._split_groups_by_extracted_name(all_groups)
        
        # Step 3.75: Split groups by year — catches cross-clustering that name-split misses
        # (e.g. "16 Wall. 36" (1873) wrongly grouped with "7 Cranch 116" (1812) because
        # both got ecn="Schooner Exchange v. McFaddon" from context/verification).
        all_groups = self._split_groups_by_year(all_groups)
        
        # Step 4: Validate and score clusters
        validated_clusters = []
        for group in all_groups:
            validation_result = validation.validate_cluster(
                group, 
                min_size=self.min_cluster_size
            )
            
            # CRITICAL FIX: Always create clusters, even if validation fails
            # Single citations and failed validations should still be returned
            # Just mark them with appropriate flags
            if len(group) >= self.min_cluster_size:
                # Propagate metadata
                propagation.propagate_metadata(group)
                
                # Calculate confidence
                confidence = validation.calculate_cluster_confidence(group)
                
                # Extract best case name and year from group
                best_case_name = propagation._select_best_case_name(group)
                best_year = propagation._select_best_year(group)
                
                # Extract extracted_name (from document) and canonical_name (from verification)
                # by scanning citations in the group
                extracted_name = None
                extracted_date = None
                canonical_name = None
                canonical_date = None
                canonical_url = None
                cluster_members = []
                
                for cit in group:
                    cit_text = propagation._get_attr(cit, "citation", "")
                    if cit_text:
                        cluster_members.append(cit_text)
                    
                    # Get best extracted_case_name from group
                    if not extracted_name or extracted_name == "N/A":
                        ecn = propagation._get_attr(cit, "extracted_case_name")
                        if ecn and ecn != "N/A":
                            ecn = _clean_ecn(ecn)
                            if ecn and ecn != "N/A":
                                extracted_name = ecn
                    
                    # Get best extracted_date from group
                    if not extracted_date:
                        ed = propagation._get_attr(cit, "extracted_date")
                        if ed and ed != "N/A":
                            extracted_date = ed
                    
                    # Get canonical data from verified citations
                    if not canonical_name or canonical_name == "N/A":
                        cn = propagation._get_attr(cit, "canonical_name")
                        if cn and cn != "N/A":
                            canonical_name = cn
                    if not canonical_date:
                        cd = propagation._get_attr(cit, "canonical_date")
                        if cd:
                            canonical_date = cd
                    if not canonical_url:
                        cu = propagation._get_attr(cit, "canonical_url")
                        if cu:
                            canonical_url = cu
                
                cluster_dict = {
                    "cluster_id": f"cluster_{len(validated_clusters)}",
                    "citations": group,
                    "size": len(group),
                    "cluster_size": len(group),
                    "confidence": confidence,
                    "validation": validation_result,
                    "is_validated": validation_result.get("valid", False),
                    # Fields expected by pipeline and frontend
                    "case_name": best_case_name,
                    "cluster_case_name": best_case_name,
                    "year": best_year,
                    "cluster_year": best_year,
                    "extracted_name": extracted_name or best_case_name or "N/A",
                    "extracted_date": extracted_date or best_year,
                    "canonical_name": canonical_name,
                    "canonical_date": canonical_date,
                    "canonical_url": canonical_url,
                    "cluster_members": cluster_members,
                }
                
                validated_clusters.append(cluster_dict)
        
        logger.info(f"[CLUSTERING] Created {len(validated_clusters)} validated clusters")
        return validated_clusters

    def _merge_groups(
        self, 
        parallel_groups: List[List[Any]], 
        structural_groups: List[List[Any]]
    ) -> List[List[Any]]:
        """Merge parallel and structural groups, removing duplicates."""
        # Use frozenset of citation IDs for deduplication
        seen = set()
        merged = []
        
        for group in parallel_groups + structural_groups:
            # Use normalized citation key (e.g. Wash. 2d -> Wn.2d) so same-case groups merge
            key = frozenset(self._get_citation_key(c) for c in group)
            
            if key not in seen:
                seen.add(key)
                merged.append(group)
        
        return merged

    def _get_citation_key(self, c: Any) -> str:
        """Stable key for a citation (dict or object). Normalize state reporter variants so
        e.g. 166 Wash. 2d 264 and 166 Wn.2d 264 merge (same case, same reporter)."""
        raw = (c.get("citation") or c.get("text") or str(c)).strip() if isinstance(c, dict) else (getattr(c, "citation", None) or getattr(c, "text", None) or str(c)).strip()
        if not raw:
            return raw
        # Normalize Washington reporter abbreviations to one form for merge/key purposes
        key = re.sub(r"\bWash\.\s*2d\b", "Wn.2d", raw, flags=re.IGNORECASE)
        key = re.sub(r"\bWash\.\s*App\.\s*2d\b", "Wn. App. 2d", key, flags=re.IGNORECASE)
        key = re.sub(r"\s+", " ", key).strip()
        return key

    def _extract_year(self, c: Any) -> Optional[int]:
        """Extract 4-digit year from citation (dict or object)."""
        for key in ("extracted_date", "canonical_date", "date"):
            val = propagation._get_attr(c, key)
            if val:
                m = re.search(r"(1[7-9]|20)\d{2}", str(val))
                if m:
                    return int(m.group(0))
        return None

    def _merge_groups_transitive(self, groups: List[List[Any]]) -> List[List[Any]]:
        """
        Merge groups that share at least one citation (transitive closure).

        Uses Union-Find for O(g × α(g)) instead of the previous O(g³) iterative
        restart-on-change approach, which hung for 250+ seconds on 838-citation docs.

        Phase 1: union groups that share an exact citation key.
        Phase 2: union groups with the same public-domain base or same case name
                 (using one representative name per group — not citation-by-citation).
        """
        if not groups or len(groups) <= 1:
            return groups

        n = len(groups)
        parent = list(range(n))
        rank = [0] * n

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]  # path halving
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px == py:
                return
            if rank[px] < rank[py]:
                px, py = py, px
            parent[py] = px
            if rank[px] == rank[py]:
                rank[px] += 1

        # Precompute per-group data once (avoids repeated recomputation inside loops)
        group_keys = [{self._get_citation_key(c) for c in g} for g in groups]
        group_years = [{self._extract_year(c) for c in g} - {None} for g in groups]
        group_segs = [{_get_segment_id(c) for c in g} - {None} for g in groups]
        group_rep_name = [self._best_name_from_group(g) for g in groups]
        group_bases = [self._extract_base_citations(g) for g in groups]

        from src.utils.same_case import names_are_same_case as _nsc

        def segments_compatible(i: int, j: int) -> bool:
            si, sj = group_segs[i], group_segs[j]
            return not (si and sj and not (si & sj))

        def years_conflict(i: int, j: int) -> bool:
            yi, yj = group_years[i], group_years[j]
            if not yi or not yj:
                return False
            if any(abs(a - b) <= 2 for a in yi for b in yj):
                return False
            # Allow same canonical name across years (e.g. CFE I + CFE II)
            ni, nj = group_rep_name[i], group_rep_name[j]
            if ni and nj and _nsc(ni.lower(), nj.lower()):
                return False
            return True

        # Phase 1: union groups sharing an exact citation key
        key_to_groups: Dict[str, List[int]] = {}
        for i in range(n):
            for k in group_keys[i]:
                if k:
                    key_to_groups.setdefault(k, []).append(i)

        for _k, idxs in key_to_groups.items():
            unique_roots = list({find(i) for i in idxs})
            if len(unique_roots) <= 1:
                continue
            base = unique_roots[0]
            for other in unique_roots[1:]:
                if find(base) == find(other):
                    continue
                if not segments_compatible(base, other):
                    continue
                if years_conflict(base, other):
                    continue
                ni, nj = group_rep_name[base], group_rep_name[other]
                if ni and nj and not _nsc(ni, nj):
                    logger.debug(
                        "[CLUSTERING] Skip union (shared key, different case: '%s' vs '%s')",
                        ni[:30], nj[:30],
                    )
                    continue
                union(base, other)

        # Phase 2a: union groups with shared public-domain base citation.
        # O(g²) but O(1) set-intersection per pair — only a tiny fraction of groups have bases.
        for i in range(n):
            for j in range(i + 1, n):
                if not group_bases[i] or not group_bases[j]:
                    continue
                if find(i) == find(j):
                    continue
                if not (group_bases[i] & group_bases[j]):
                    continue
                if not segments_compatible(i, j):
                    continue
                if years_conflict(i, j):
                    continue
                union(i, j)
                logger.debug("[CLUSTERING] Union groups %d,%d (shared base citation)", i, j)

        # Phase 2b: union groups with same case name, bucketed by normalized first-party word.
        # Bucketing reduces comparisons from O(g²) to O(g × avg_bucket_size²).
        # Without bucketing, names_are_same_case() costs ~0.23ms each × g² calls = tens of seconds.
        def _first_word_key(name: str) -> str:
            """First significant word from the plaintiff portion (before ' v. ')."""
            part = name.split(" v. ", 1)[0] if " v. " in name else name
            words = re.sub(r"[^\w\s]", " ", part.lower()).split()
            stop = {"the", "in", "re", "a", "an", "of"}
            for w in words:
                if len(w) >= 3 and w not in stop:
                    return w
            return part.lower()[:8] if part else "__"

        from collections import defaultdict as _dd
        bucket: dict = _dd(list)
        for i in range(n):
            ni = group_rep_name[i]
            if ni:
                bucket[_first_word_key(ni)].append(i)

        for _bkey, bidxs in bucket.items():
            if len(bidxs) < 2:
                continue
            for a in range(len(bidxs)):
                i = bidxs[a]
                for b in range(a + 1, len(bidxs)):
                    j = bidxs[b]
                    if find(i) == find(j):
                        continue
                    if group_keys[i] & group_keys[j]:
                        continue  # handled in Phase 1
                    if not segments_compatible(i, j):
                        continue
                    if years_conflict(i, j):
                        continue
                    ni, nj = group_rep_name[i], group_rep_name[j]
                    if ni and nj and _nsc(ni, nj):
                        union(i, j)
                        logger.debug(
                            "[CLUSTERING] Union groups %d,%d (same case: '%s' ~ '%s')",
                            i, j, ni[:30], nj[:30],
                        )

        # Rebuild merged groups from Union-Find, deduplicating by citation key
        from collections import defaultdict
        root_to_citations: Dict[int, List[Any]] = defaultdict(list)
        for i, g in enumerate(groups):
            root_to_citations[find(i)].extend(g)

        result = []
        for g in root_to_citations.values():
            seen_keys: set = set()
            deduped = []
            for c in g:
                k = self._get_citation_key(c)
                if k not in seen_keys:
                    seen_keys.add(k)
                    deduped.append(c)
            result.append(deduped)

        if len(result) < len(groups):
            logger.info(
                "[CLUSTERING] Transitive merge: %d groups -> %d "
                "(parallel groups sharing a citation or same case merged)",
                len(groups), len(result),
            )
        return result

    def _best_name_from_group(self, group: List[Any]) -> str:
        """Return the best representative case name for a group (canonical preferred)."""
        for c in group:
            cn = (propagation._get_attr(c, "canonical_name") or "").strip()
            if cn and " v. " in cn:
                return cn
        for c in group:
            ecn = _clean_ecn(propagation._get_attr(c, "extracted_case_name") or "")
            if ecn and ecn != "N/A":
                return ecn
        return ""

    def _extract_base_citations(self, group: List[Any]) -> set:
        """Precompute the set of public-domain base citation strings for a group."""
        bases: set = set()
        for c in group:
            text = (propagation._get_attr(c, "citation") or "").strip()
            if not text:
                continue
            for m in detection._PUBLIC_DOMAIN_BASE_RE.finditer(text):
                base = next(grp for grp in m.groups() if grp)
                bases.add(base.strip().lower())
        return bases

    def _split_groups_by_extracted_name(self, groups: List[List[Any]]) -> List[List[Any]]:
        """
        Split proximity groups where citations have different extracted_case_name values.
        
        Proximity detection groups nearby citations together, but citations for
        different cases may appear close together in text (e.g., "Larimore v. Blaylock,
        259 Va. 568 ... Swindle v. State, 10 Tenn. 581"). This method splits such
        groups so each case gets its own cluster.
        """
        result = []
        for group in groups:
            if len(group) <= 1:
                result.append(group)
                continue
            
            # Collect extracted_case_name for each citation
            name_to_cits: Dict[str, List[Any]] = {}
            no_name_cits: List[Any] = []
            
            for cit in group:
                ecn = propagation._get_attr(cit, "extracted_case_name", "") or ""
                ecn = _clean_ecn(ecn)
                cit_text = propagation._get_attr(cit, "citation", "")
                logger.debug(f"[SPLIT-DEBUG] Citation '{cit_text}' ecn='{ecn}'")
                if ecn and ecn != "N/A" and " v. " in ecn:
                    # Normalize: lowercase, strip whitespace
                    norm = re.sub(r"\s+", " ", ecn.strip().lower())
                    
                    # Find matching group using names_are_same_case (handles
                    # corporate suffixes like Inc., Corp., LLC correctly)
                    from src.utils.same_case import names_are_same_case as _nsc
                    matched = False
                    for key in list(name_to_cits.keys()):
                        if _nsc(norm, key):
                            name_to_cits[key].append(cit)
                            matched = True
                            break
                    if not matched:
                        name_to_cits[norm] = [cit]
                else:
                    no_name_cits.append(cit)
            
            # If all citations have the same name (or no names), keep as one group
            if len(name_to_cits) <= 1:
                logger.debug(f"[SPLIT-DEBUG] Group of {len(group)}: {len(name_to_cits)} named, {len(no_name_cits)} no-name -> keeping as one")
                result.append(group)
                continue
            
            # Split into separate groups
            logger.info(
                f"[CLUSTER-SPLIT-ECN] Splitting group of {len(group)} into "
                f"{len(name_to_cits)} groups: {list(name_to_cits.keys())}"
            )
            
            # Try to assign no-name citations to a matching named group
            # by checking if the bare citation text appears in any named citation's full text.
            # CRITICAL: Bare citation (e.g. "857 N.W.2d 569") that appears IN another citation
            # belongs to that citation's case, not the prior case. Prefer containment over
            # verification-assigned name when the bare cite is a substring of a different case.
            remaining_no_name = []
            for nn_cit in no_name_cits:
                nn_text = propagation._get_attr(nn_cit, "citation", "")
                matched_to_group = False
                if nn_text:
                    for name, cits in name_to_cits.items():
                        for named_cit in cits:
                            named_text = propagation._get_attr(named_cit, "citation", "")
                            if nn_text and named_text and nn_text in named_text:
                                cits.append(nn_cit)
                                matched_to_group = True
                                break
                        if matched_to_group:
                            break
                if not matched_to_group:
                    # Fallback: shared public domain base citation
                    for name, cits in name_to_cits.items():
                        if any(detection._shared_base_citation(nn_cit, nc) for nc in cits):
                            cits.append(nn_cit)
                            matched_to_group = True
                            break
                if not matched_to_group:
                    remaining_no_name.append(nn_cit)

            # Also reassign named citations when bare cite is substring: "857 N.W.2d 569"
            # with Dow's name should go to Frederick if "857 N.W.2d 569" is in Frederick's citation
            for name, cits in list(name_to_cits.items()):
                to_move = []
                for cit in cits:
                    cit_text = propagation._get_attr(cit, "citation", "")
                    if not cit_text or len(cit_text) > 50:
                        continue
                    for other_name, other_cits in name_to_cits.items():
                        if other_name == name:
                            continue
                        for oc in other_cits:
                            oc_text = propagation._get_attr(oc, "citation", "")
                            if cit_text in oc_text and cit_text != oc_text:
                                to_move.append((cit, other_cits))
                                break
                for cit, target in to_move:
                    cits.remove(cit)
                    target.append(cit)
            
            for name, cits in name_to_cits.items():
                result.append(cits)
            
            # Unmatched no-name citations become standalone groups
            for nn_cit in remaining_no_name:
                result.append([nn_cit])
        
        return result

    def _split_groups_by_year(self, groups: List[List[Any]]) -> List[List[Any]]:
        """
        Split groups where citations have extracted dates spanning more than 30 years.
        
        Catches cross-clustering that name-split misses: e.g. "16 Wall. 36" (1873)
        grouped with "7 Cranch 116" (1812) because both got ecn="Schooner Exchange".
        Parallel citations for the same case are always from the same year.
        """
        MAX_YEAR_SPAN = 30
        result = []
        split_count = 0
        groups_checked = 0
        for group in groups:
            if len(group) <= 1:
                result.append(group)
                continue
            groups_checked += 1
            # Extract years for each citation
            year_cit_pairs = []
            for c in group:
                y = self._extract_year(c)
                year_cit_pairs.append((y, c))
            years_present = {y for y, _ in year_cit_pairs if y}
            if len(years_present) <= 1:
                result.append(group)
                continue
            min_y, max_y = min(years_present), max(years_present)
            if max_y - min_y > MAX_YEAR_SPAN:
                cit_summaries = [
                    f"{(propagation._get_attr(c, 'citation', '') or '')[:30]}(y={y})"
                    for y, c in year_cit_pairs
                ]
                logger.info(
                    f"[CLUSTER-SPLIT-YEAR] Candidate group span={max_y - min_y}: {cit_summaries[:4]}"
                )
            if max_y - min_y <= MAX_YEAR_SPAN:
                result.append(group)
                continue
            # Year span too large: split into sub-groups by clustering years
            # Simple approach: sort by year and split at gaps > MAX_YEAR_SPAN
            sorted_years = sorted(years_present)
            year_to_bucket = {}
            bucket_id = 0
            year_to_bucket[sorted_years[0]] = bucket_id
            for i in range(1, len(sorted_years)):
                if sorted_years[i] - sorted_years[i - 1] > MAX_YEAR_SPAN:
                    bucket_id += 1
                year_to_bucket[sorted_years[i]] = bucket_id
            buckets: Dict[int, List[Any]] = {}
            no_year: List[Any] = []
            for y, c in year_cit_pairs:
                if y is None:
                    no_year.append(c)
                else:
                    b = year_to_bucket[y]
                    buckets.setdefault(b, []).append(c)
            # Assign no-year citations to the largest bucket
            if no_year and buckets:
                largest = max(buckets, key=lambda k: len(buckets[k]))
                buckets[largest].extend(no_year)
            elif no_year:
                buckets[0] = no_year
            if len(buckets) > 1:
                cit_texts = [
                    (propagation._get_attr(c, "citation", "") or "")[:30]
                    for c in group
                ]
                logger.info(
                    f"[CLUSTER-SPLIT-YEAR] Splitting group of {len(group)} into "
                    f"{len(buckets)} sub-groups (year span {min_y}-{max_y}): "
                    f"{cit_texts[:4]}"
                )
                split_count += 1
            for b_cits in buckets.values():
                result.append(b_cits)
        logger.info(
            f"[CLUSTER-SPLIT-YEAR] Checked {groups_checked} multi-citation groups, split {split_count}"
        )
        return result

    def _extract_document_primary_case_name(self, text: str) -> Optional[str]:
        """
        Extract the primary case name from the document header.
        
        The primary case name typically appears at the beginning of legal documents in formats like:
        - "PLAINTIFF v. DEFENDANT"
        - "In the Matter of CASE NAME"
        - In briefs: "CASE NAME\nNo. 12-3456"
        
        This is used for contamination filtering to prevent cited case names from being
        incorrectly extracted as the document's own case name.
        
        Args:
            text: Full document text
            
        Returns:
            The document's primary case name, or None if not found
        """
        if not text or len(text) < 50:
            return None
        
        # Look at first 2000 characters (enough for case caption)
        header = text[:2000]
        
        # Strategy 1: Look for case name pattern before "No." (case number)
        case_number_match = re.search(r'No\.\s+\d{2,4}-\d{3,5}', header, re.IGNORECASE)
        if case_number_match:
            # Look backwards from case number for case name
            before_case_num = header[:case_number_match.start()]
            
            # Look for "Plaintiffs" or "Plaintiff" marker
            plaintiffs_marker = re.search(r'Plaintiffs?\s*[-]\s*Appellants?', before_case_num, re.IGNORECASE)
            if plaintiffs_marker:
                # Extract from start to plaintiffs marker
                plaintiff_section = before_case_num[:plaintiffs_marker.start()].strip()
                # Take last 500 chars to get the plaintiff names
                plaintiff_section = plaintiff_section[-500:]
                
                # Find first complete party name (handles "COMPANY NAME, a corp; PERSON NAME, individual")
                # Look for pattern: ALL CAPS NAME followed by comma or semicolon
                first_party = re.search(r'([A-Z][A-Z\s&\.,\'-]{8,100}?)(?:,|\;)', plaintiff_section, re.DOTALL)
                if first_party:
                    plaintiff_name = first_party.group(1).strip()
                    # Clean up trailing punctuation and descriptions
                    plaintiff_name = re.sub(r',\s*a\s+.*$', '', plaintiff_name)
                    plaintiff_name = re.sub(r',\s*an\s+.*$', '', plaintiff_name)
                    plaintiff_name = plaintiff_name.strip().strip(',').strip()
                    
                    # Find defendant after plaintiffs marker
                    after_plaintiffs = before_case_num[plaintiffs_marker.end():]
                    v_match = re.search(r'v\.\s*([A-Z][A-Za-z\s\.,&\-\']{5,80})', after_plaintiffs, re.IGNORECASE)
                    if v_match:
                        defendant_name = v_match.group(1).strip()
                        # Clean defendant name
                        defendant_name = re.sub(r',\s*(?:an?\s+)?individual.*$', '', defendant_name, flags=re.IGNORECASE)
                        defendant_name = defendant_name.strip().strip(',').strip()
                        
                        case_name = f"{plaintiff_name} v. {defendant_name}"
                        logger.info(f"[CONTAMINATION-FILTER] Found primary case: '{case_name}'")
                        return case_name
            
            # Fallback: single-plaintiff logic
            v_pattern = re.search(r'([A-Z][A-Za-z\s\.,&\-\']{5,80})\s+v\.\s+([A-Z][A-Za-z\s\.,&\-\']{5,80})', before_case_num, re.IGNORECASE)
            if v_pattern:
                case_name = f"{v_pattern.group(1).strip()} v. {v_pattern.group(2).strip()}"
                logger.info(f"[CONTAMINATION-FILTER] Found primary case: '{case_name}'")
                return case_name
        
        # Strategy 2: Look for case name in first few lines
        lines = header.split('\n')
        for i, line in enumerate(lines[:30]):
            line = line.strip()
            if ' v. ' in line and len(line) > 10 and len(line) < 150:
                # Skip lines that contain citation patterns (volume reporter page)
                if re.search(r'\d+\s+\w+\.\s*\d*\s+\d+', line):
                    continue
                # Skip lines starting with signal words (e.g., "See United States v. ...")
                if re.match(r'^(?:See|Cf\.|Compare|But see|Accord)', line, re.IGNORECASE):
                    continue
                # Skip syllabus boilerplate text
                if any(phrase in line.lower() for phrase in ['syllabus', 'reporter of decisions', 'headnote', 'slip opinion']):
                    continue
                # Clean up common patterns
                cleaned = re.sub(r'^\s*(?:IN\s+THE\s+)?(?:MATTER\s+OF\s+)?', '', line, flags=re.IGNORECASE)
                cleaned = re.sub(r'\s*,?\s*(?:Appellant|Appellee|Plaintiff|Defendant|Petitioner|Respondent)s?\s*$', '', cleaned, flags=re.IGNORECASE)
                
                if ' v. ' in cleaned and len(cleaned) > 10:
                    logger.info(f"[CONTAMINATION-FILTER] Found primary case: '{cleaned}'")
                    return cleaned
        
        # Strategy 3: Pattern match for common formats
        pattern = r'([A-Z][A-Za-z\s\.,&\-\']{8,80})\s+v\.\s+([A-Za-z][A-Za-z\s\.,&\-\']{8,80})(?:\s*,|\s+No\.)'
        match = re.search(pattern, header)
        if match:
            case_name = f"{match.group(1).strip()} v. {match.group(2).strip()}"
            logger.info(f"[CONTAMINATION-FILTER] Found primary case: '{case_name}'")
            return case_name
        
        logger.debug("[CONTAMINATION-FILTER] Could not extract document primary case name")
        return None


# Module-level convenience function
def cluster_citations_unified_master(
    citations: List[Any],
    original_text: str = "",
    enable_verification: bool = None,
    request_id: str = "",
    config: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, str, str], None]] = None
) -> List[Dict[str, Any]]:
    """
    THE SINGLE, UNIFIED CLUSTERING FUNCTION (MODULAR VERSION).
    
    This function replaces ALL 45+ duplicate clustering functions.
    Uses the new modular clustering package internally.
    
    Returns:
        List of cluster dictionaries with comprehensive metadata
    """
    clusterer = UnifiedClusteringMaster(config)
    return clusterer.cluster_citations(
        citations, 
        original_text, 
        enable_verification, 
        request_id, 
        progress_callback
    )
