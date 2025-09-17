"""
Citation Deduplication Utilities
Provides consistent deduplication logic for both sync and async processing pipelines.
"""

import logging
from typing import List, Dict, Any, Set
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

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
    
    if debug:
        logger.info(f"[Deduplication] After position overlaps: {len(step3_results)} citations")
    
    # Step 4: Remove similar case name + date combinations
    final_results = _remove_similar_citations(step3_results, debug)
    
    if debug:
        logger.info(f"[Deduplication] Final result: {len(final_results)} citations")
        logger.info(f"[Deduplication] Removed {len(citations) - len(final_results)} duplicates total")
    
    return final_results

def _get_citation_text(citation: Dict[str, Any]) -> str:
    """Extract citation text from citation dictionary."""
    return str(citation.get('citation', citation.get('citation_text', str(citation))))

def _normalize_citation_text(citation_text: str) -> str:
    """Normalize citation text for comparison."""
    # Remove extra whitespace, newlines, and normalize spacing
    normalized = ' '.join(citation_text.replace('\n', ' ').replace('\r', ' ').split())
    # Remove common formatting variations
    normalized = normalized.replace(' . ', '.').replace('  ', ' ')
    return normalized.strip().lower()

def _remove_position_overlaps(citations: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """Remove citations that overlap in position."""
    # Only process if we have position data
    positioned_citations = []
    non_positioned_citations = []
    
    for citation in citations:
        start_pos = citation.get('start_index') or citation.get('start_pos')
        end_pos = citation.get('end_index') or citation.get('end_pos')
        
        if start_pos is not None and end_pos is not None:
            positioned_citations.append(citation)
        else:
            non_positioned_citations.append(citation)
    
    if not positioned_citations:
        return citations  # No position data, skip this step
    
    # Sort by position and confidence
    positioned_citations.sort(key=lambda x: (
        x.get('start_index') or x.get('start_pos') or 0,
        -(x.get('confidence', 0) or x.get('confidence_score', 0) or 0)
    ))
    
    deduplicated_positioned = [positioned_citations[0]]
    
    for citation in positioned_citations[1:]:
        start_pos = citation.get('start_index') or citation.get('start_pos')
        end_pos = citation.get('end_index') or citation.get('end_pos')
        
        overlaps = False
        for existing in deduplicated_positioned:
            existing_start = existing.get('start_index') or existing.get('start_pos')
            existing_end = existing.get('end_index') or existing.get('end_pos')
            
            if (start_pos < existing_end and end_pos > existing_start):
                overlaps = True
                if debug:
                    logger.info(f"[Deduplication] Removed position overlap: {_get_citation_text(citation)}")
                break
        
        if not overlaps:
            deduplicated_positioned.append(citation)
    
    return deduplicated_positioned + non_positioned_citations

def _remove_similar_citations(citations: List[Dict[str, Any]], debug: bool = False) -> List[Dict[str, Any]]:
    """Remove citations with very similar case names and dates."""
    if len(citations) <= 1:
        return citations
    
    # Sort by confidence to keep highest confidence versions
    citations.sort(key=lambda x: -(x.get('confidence', 0) or x.get('confidence_score', 0) or 0))
    
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
                    logger.info(f"[Deduplication] Removed similar citation: {_get_citation_text(citation)} "
                              f"(similarity: {name_similarity:.2f}, date_match: {date_match})")
                break
        
        if not is_similar:
            deduplicated.append(citation)
    
    return deduplicated

def _get_case_name(citation: Dict[str, Any]) -> str:
    """Extract case name from citation dictionary."""
    name = (citation.get('case_name') or 
            citation.get('extracted_case_name') or 
            citation.get('canonical_name') or 
            '')
    return str(name).lower().strip()

def _get_date(citation: Dict[str, Any]) -> str:
    """Extract date from citation dictionary."""
    date = (citation.get('extracted_date') or 
            citation.get('canonical_date') or 
            citation.get('year') or 
            '')
    return str(date).strip() if date else ''

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
    clusters.sort(key=lambda x: -len(x.get('citations', []) or x.get('citation_objects', [])))
    
    deduplicated_clusters = []
    used_citations = set()
    
    for cluster in clusters:
        cluster_citations = cluster.get('citations', []) or cluster.get('citation_objects', [])
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
            logger.info(f"[Cluster Deduplication] Removed overlapping cluster "
                       f"({overlap}/{len(cluster_citation_texts)} citations overlap)")
    
    if debug:
        logger.info(f"[Cluster Deduplication] Final result: {len(deduplicated_clusters)} clusters")
    
    return deduplicated_clusters
