"""
Citation Deduplication Utilities
Provides consistent deduplication logic for both sync and async processing pipelines.
"""

import re
import logging
from typing import List, Dict, Any
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# PERFORMANCE OPTIMIZATION: Pre-compile regex patterns used frequently
# This avoids recompiling patterns on every function call (10-100x speedup)
_RE_TRAILING_PAGE = re.compile(r"(\d{1,6})\s*$")
_RE_LEADING_VOLUME = re.compile(r"^(\d+)\s+(.*)$")
_RE_NON_ALPHANUM = re.compile(r"[^a-z0-9\s\.]")
_RE_WHITESPACE = re.compile(r"\s+")
_RE_LEADING_DIGIT = re.compile(r"^\d+\b")


def deduplicate_citations(citations: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """
    Remove duplicate citations using multiple strategies:
    1. Exact citation text match
    2. Normalized citation text match
    3. Position overlap (if available)
    4. Case name + date similarity

    Args:
        citations: List of citation dictionaries
        debug: Enable debug logging

    Returns:
        List of deduplicated citations
    """
    if not citations:
        return []

    if debug:
        logger.info(f"[Deduplication] Starting with {len(citations)} citations")

    # Step 1: Remove exact duplicates by citation text
    seen_citations = set()
    step1_results = []

    for citation in citations:
        citation_text = _get_citation_text(citation)
        if citation_text not in seen_citations:
            seen_citations.add(citation_text)
            step1_results.append(citation)
        elif debug:
            logger.info(f"[Deduplication] Removed exact duplicate: {citation_text}")

    if debug:
        logger.info(f"[Deduplication] After exact duplicates: {len(step1_results)} citations")

    # Step 2: Remove normalized duplicates (handle whitespace/formatting differences)
    step2_results = []
    seen_normalized = set()

    for citation in step1_results:
        normalized = _normalize_citation_text(_get_citation_text(citation))
        if normalized not in seen_normalized:
            seen_normalized.add(normalized)
            step2_results.append(citation)
        elif debug:
            logger.info(f"[Deduplication] Removed normalized duplicate: {_get_citation_text(citation)}")

    if debug:
        logger.info(f"[Deduplication] After normalized duplicates: {len(step2_results)} citations")

    # Step 3: Remove position overlaps (if position data available)
    step3_results = _remove_position_overlaps(step2_results, debug)

    # Step 3.5: Collapse truncated reporter variants (e.g., "Cal. 3d 574" vs "11 Cal. 3d 574")
    step35_results = _dedup_truncated_reporter_variants(step3_results, debug)

    if debug:
        logger.info(f"[Deduplication] After position overlaps: {len(step3_results)} citations")

    # Step 4: Remove similar case name + date combinations
    final_results = _remove_similar_citations(step35_results, debug)

    if debug:
        logger.info(f"[Deduplication] Final result: {len(final_results)} citations")
        logger.info(f"[Deduplication] Removed {len(citations) - len(final_results)} duplicates total")

    return final_results


def _get_citation_text(citation: Dict[str, Any]) -> str:
    """Extract citation text from citation dictionary."""
    return str(citation.get("citation", citation.get("citation_text", str(citation))))


def _normalize_citation_text(citation_text: str) -> str:
    """Normalize citation text for comparison."""
    # Remove extra whitespace, newlines, and normalize spacing
    normalized = " ".join(citation_text.replace("\n", " ").replace("\r", " ").split())
    # Remove common formatting variations
    normalized = normalized.replace(" . ", ".").replace("  ", " ")
    return normalized.strip().lower()


def _remove_position_overlaps(citations: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """Remove citations that overlap in position using efficient sweep line algorithm."""
    # Only process if we have position data
    positioned_citations = []
    non_positioned_citations = []

    for citation in citations:
        start_pos = citation.get("start_index") or citation.get("start_pos")
        end_pos = citation.get("end_index") or citation.get("end_pos")

        if start_pos is not None and end_pos is not None:
            positioned_citations.append((start_pos, end_pos, citation))
        else:
            non_positioned_citations.append(citation)

    if not positioned_citations:
        return citations  # No position data, skip this step

    # Sort by start position, then by confidence (descending)
    positioned_citations.sort(
        key=lambda x: (
            x[0],  # start_pos
            -(x[2].get("confidence", 0) or x[2].get("confidence_score", 0) or 0),  # confidence
        )
    )

    # Sweep line algorithm: track active intervals
    # Only keep citations that don't overlap with higher-confidence citations
    deduplicated = []
    active_intervals = []  # List of (end_pos, citation) that are still "active"

    for start_pos, end_pos, citation in positioned_citations:
        # Remove intervals that have ended before this one starts
        active_intervals = [(e, c) for e, c in active_intervals if e > start_pos]

        # Check if this citation overlaps with any active interval
        overlaps = False
        for active_end, active_citation in active_intervals:
            if end_pos > active_citation.get("start_index") or end_pos > active_citation.get("start_pos"):
                # Overlap detected - this citation is lower confidence (due to sorting)
                overlaps = True
                if debug:
                    logger.info(f"[Deduplication] Removed position overlap: {_get_citation_text(citation)}")
                break

        if not overlaps:
            deduplicated.append(citation)
            active_intervals.append((end_pos, citation))

    return deduplicated + non_positioned_citations


def _dedup_truncated_reporter_variants(citations: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """Collapse duplicates where one variant lacks a leading volume number but shares reporter + page.

    Examples:
      - "Cal. 3d 574" vs "11 Cal. 3d 574" -> keep the one with volume (11 Cal. 3d 574)
      - "Ill. App. 3d 691" vs "389 Ill. App. 3d 691" -> keep the volume variant

    Strategy:
      - Build a key reporter_series + page, ignoring any leading volume number
      - Prefer variant that begins with a volume number; break ties by longer citation text
    """
    if not citations:
        return citations

    buckets: Dict[str, Dict[str, Any]] = {}

    def make_key(cit_text: str) -> str | None:
        if not cit_text:
            return None
        s = " ".join(str(cit_text).replace("\n", " ").replace("\r", " ").split()).strip()
        s_low = s.lower()
        # Extract trailing page number
        m_page = _RE_TRAILING_PAGE.search(s_low)
        if not m_page:
            return None
        page = m_page.group(1)
        # Remove leading volume number if present
        s_no_page = s_low[: m_page.start()].strip()
        m_vol = _RE_LEADING_VOLUME.match(s_no_page)
        reporter = m_vol.group(2) if m_vol else s_no_page
        # Normalize whitespace and punctuation in reporter
        reporter = _RE_NON_ALPHANUM.sub(" ", reporter)
        reporter = _RE_WHITESPACE.sub(" ", reporter).strip()
        if not reporter:
            return None
        return f"{reporter}::{page}"

    def has_leading_volume(cit_text: str) -> bool:
        if not cit_text:
            return False
        s = str(cit_text).lstrip()
        return bool(_RE_LEADING_DIGIT.match(s))

    for cit in citations:
        text = _get_citation_text(cit)
        key = make_key(text)
        if not key:
            # Not a recognizable reporter+page; keep as-is in final pass
            buckets.setdefault("__passthru__", {"items": []})["items"].append(cit)
            continue
        entry = buckets.get(key)
        if not entry:
            buckets[key] = {"best": cit}
            continue
        # Decide which to prefer
        current_best = entry["best"]
        best_text = _get_citation_text(current_best)
        # Prefer with leading volume
        candidate_has_vol = has_leading_volume(text)
        best_has_vol = has_leading_volume(best_text)
        choose_candidate = False
        if candidate_has_vol and not best_has_vol:
            choose_candidate = True
        elif candidate_has_vol == best_has_vol:
            # Tie-breaker: longer text
            choose_candidate = len(text) > len(best_text)
        if choose_candidate:
            entry["best"] = cit

    # Rebuild list: take best from each bucket + passthru
    result: List[Dict[str, Any]] = []
    for key, entry in buckets.items():
        if key == "__passthru__":
            result.extend(entry["items"])
        else:
            result.append(entry["best"])

    if debug:
        removed = len(citations) - len(result)
        if removed > 0:
            logger.info(f"[Deduplication] Truncated reporter variants removed: {removed}")

    return result


def _remove_similar_citations(citations: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """Remove citations with very similar case names and dates."""
    if len(citations) <= 1:
        return citations

    # Sort by confidence to keep highest confidence versions
    citations.sort(key=lambda x: -(x.get("confidence", 0) or x.get("confidence_score", 0) or 0))

    deduplicated = [citations[0]]

    for citation in citations[1:]:
        is_similar = False
        citation_name = _get_case_name(citation)
        citation_date = _get_date(citation)

        for existing in deduplicated:
            existing_name = _get_case_name(existing)
            existing_date = _get_date(existing)

            # Check name similarity
            name_similarity = _calculate_similarity(citation_name, existing_name)

            # Check date match
            date_match = citation_date and existing_date and citation_date == existing_date

            # Consider similar if high name similarity and same date, or very high name similarity
            if (name_similarity > 0.85 and date_match) or name_similarity > 0.95:
                is_similar = True
                if debug:
                    logger.info(
                        f"[Deduplication] Removed similar citation: {_get_citation_text(citation)} "
                        f"(similarity: {name_similarity:.2f}, date_match: {date_match})"
                    )
                break

        if not is_similar:
            deduplicated.append(citation)

    return deduplicated


def _get_case_name(citation: Dict[str, Any]) -> str:
    """Extract case name from citation dictionary - USE ONLY EXTRACTED, NEVER CANONICAL!"""
    name = citation.get("case_name") or citation.get("extracted_case_name") or ""
    return str(name).lower().strip()


def _get_date(citation: Dict[str, Any]) -> str:
    """Extract date from citation dictionary - USE ONLY EXTRACTED, NEVER CANONICAL!"""
    date = citation.get("extracted_date") or citation.get("year") or ""
    return str(date).strip() if date else ""


def _calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two text strings."""
    if not text1 or not text2:
        return 0.0

    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def deduplicate_clusters(clusters: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """
    Remove duplicate clusters based on citation overlap.

    Args:
        clusters: List of cluster dictionaries
        debug: Enable debug logging

    Returns:
        List of deduplicated clusters
    """
    if not clusters:
        return []

    if debug:
        logger.info(f"[Cluster Deduplication] Starting with {len(clusters)} clusters")

    # Sort clusters by size (number of citations) to prefer larger clusters
    clusters.sort(key=lambda x: -len(x.get("citations", []) or x.get("citation_objects", [])))

    deduplicated_clusters = []
    used_citations = set()

    for cluster in clusters:
        cluster_citations = cluster.get("citations", []) or cluster.get("citation_objects", [])
        cluster_citation_texts = {_get_citation_text(c) for c in cluster_citations}

        # Check if this cluster significantly overlaps with already used citations
        overlap = len(cluster_citation_texts & used_citations)
        overlap_ratio = overlap / len(cluster_citation_texts) if cluster_citation_texts else 0

        # Keep cluster if less than 50% overlap with existing clusters
        if overlap_ratio < 0.5:
            deduplicated_clusters.append(cluster)
            used_citations.update(cluster_citation_texts)
            if debug:
                logger.info(f"[Cluster Deduplication] Kept cluster with {len(cluster_citations)} citations")
        elif debug:
            logger.info(
                f"[Cluster Deduplication] Removed overlapping cluster "
                f"({overlap}/{len(cluster_citation_texts)} citations overlap)"
            )

    if debug:
        logger.info(f"[Cluster Deduplication] Final result: {len(deduplicated_clusters)} clusters")

    return deduplicated_clusters
