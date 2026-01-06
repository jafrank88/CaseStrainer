#!/usr/bin/env python3
"""
Cross-document deduplication utility
"""

from typing import List, Dict, Any, Tuple, Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def deduplicate_clusters_cross_document(clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate clusters that appear across multiple documents.
    
    This function identifies clusters that refer to the same case but were extracted
    from different documents and merges them, preserving all source document information.
    
    Args:
        clusters: List of cluster dictionaries from multiple documents
        
    Returns:
        List of deduplicated clusters
    """
    if not clusters:
        return clusters
    
    logger.info(f"[CROSS-DEDUP] Starting with {len(clusters)} clusters")
    
    # Group clusters by canonical case information
    case_groups = defaultdict(list)
    
    for cluster in clusters:
        # Create a key for grouping based on canonical information
        # Priority: canonical_name > canonical_case_name > extracted_case_name
        case_name = (
            cluster.get('canonical_name') or 
            cluster.get('canonical_case_name') or 
            cluster.get('extracted_case_name') or 
            'Unknown'
        )
        
        # Skip clusters with no case name - they should not be deduplicated
        if not case_name or case_name == 'Unknown' or case_name == 'N/A':
            logger.debug(f"[CROSS-DEDUP] Skipping cluster with no case name")
            continue
        
        # Also use canonical_date if available
        case_date = (
            cluster.get('canonical_date') or 
            cluster.get('cluster_year') or 
            cluster.get('extracted_date') or
            ''
        )
        
        # Create normalized key
        normalized_name = _normalize_case_name(case_name)
        key = (normalized_name, str(case_date))
        
        case_groups[key].append(cluster)
    
    # Keep clusters that weren't grouped (no case name)
    ungrouped = [c for c in clusters if (
        not (c.get('canonical_name') or c.get('canonical_case_name') or c.get('extracted_case_name')) or
        (c.get('canonical_name') or c.get('canonical_case_name') or c.get('extracted_case_name')) in ('Unknown', 'N/A')
    )]
    
    # Merge duplicates with stricter criteria
    deduplicated = []
    duplicates_found = 0
    
    for (case_key, case_clusters) in case_groups.items():
        if len(case_clusters) == 1:
            # No duplicate, keep as is
            deduplicated.append(case_clusters[0])
        else:
            # Check if these are truly duplicates
            # Require either same year OR very high name similarity
            should_merge = False
            reference_name = case_clusters[0].get('canonical_name') or case_clusters[0].get('extracted_case_name', '')
            reference_date = case_clusters[0].get('canonical_date') or case_clusters[0].get('extracted_date', '')
            
            for cluster in case_clusters[1:]:
                current_name = cluster.get('canonical_name') or cluster.get('extracted_case_name', '')
                current_date = cluster.get('canonical_date') or cluster.get('extracted_date', '')
                
                # Check if years match (allow for some variation in extracted dates)
                ref_year = _extract_year(reference_date)
                cur_year = _extract_year(current_date)
                
                if ref_year and cur_year:
                    # If years are the same, allow merging with lower name similarity
                    if ref_year == cur_year:
                        name_similarity = _calculate_name_similarity(reference_name, current_name)
                        if name_similarity > 0.7:  # 70% similarity required for same year
                            should_merge = True
                            break
                    else:
                        # If years are different, require very high name similarity
                        if abs(ref_year - cur_year) > 2:  # More than 2 years difference
                            continue  # Don't merge cases with significant year differences
                        
                        name_similarity = _calculate_name_similarity(reference_name, current_name)
                        if name_similarity > 0.95:  # 95% similarity required for different years
                            should_merge = True
                            break
                else:
                    # If no year info, require very high similarity
                    name_similarity = _calculate_name_similarity(reference_name, current_name)
                    if name_similarity > 0.95:
                        should_merge = True
                        break
            
            if should_merge and len(case_clusters) > 1:
                duplicates_found += len(case_clusters) - 1
                merged = _merge_duplicate_clusters(case_clusters)
                deduplicated.append(merged)
            else:
                # Don't merge - keep all clusters separate
                deduplicated.extend(case_clusters)
    
    # Add ungrouped clusters back
    deduplicated.extend(ungrouped)
    
    logger.info(f"[CROSS-DEDUP] After deduplication: {len(deduplicated)} clusters")
    logger.info(f"[CROSS-DEDUP] Removed {duplicates_found} duplicate clusters")
    
    return deduplicated


def _normalize_case_name(name: str) -> str:
    """Normalize case name for comparison"""
    if not name:
        return ""
    
    import re
    # Remove common variations and normalize
    normalized = name.lower().strip()
    
    # Remove "v.", "vs.", "v " variations but keep the parties
    normalized = re.sub(r'\bv\.?\s+', ' v ', normalized)
    normalized = re.sub(r'\bvs\.?\s+', ' v ', normalized)
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Keep important distinguishing information like "in re" and parentheticals
    # Only remove punctuation that's not meaningful for comparison
    normalized = re.sub(r'[^\w\s\(\)]', '', normalized)
    
    return normalized.strip()


def _extract_year(date_str: str) -> Optional[int]:
    """Extract 4-digit year from date string"""
    if not date_str:
        return None
    
    import re
    # Look for 4-digit year
    match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if match:
        return int(match.group())
    
    return None


def _calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two case names"""
    if not name1 or not name2:
        return 0.0
    
    from difflib import SequenceMatcher
    
    # Normalize both names for comparison
    norm1 = _normalize_case_name(name1)
    norm2 = _normalize_case_name(name2)
    
    # Calculate sequence similarity
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Bonus for exact matches
    if norm1 == norm2:
        return 1.0
    
    # Penalty for very different lengths
    len_ratio = min(len(norm1), len(norm2)) / max(len(norm1), len(norm2))
    similarity *= len_ratio
    
    return similarity


def _merge_duplicate_clusters(clusters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple clusters that refer to the same case.
    
    The merge strategy:
    1. Keep the cluster with the best verification status as the base
    2. Merge citations from all clusters
    3. Combine source document information
    4. Keep the best metadata (canonical names, dates, URLs)
    """
    if not clusters:
        return {}
    
    if len(clusters) == 1:
        return clusters[0]
    
    # Sort clusters by verification status and confidence
    def get_cluster_score(cluster):
        score = 0
        if cluster.get('verification_status') == 'verified':
            score += 100
        elif cluster.get('verification_status') == 'possible_match':
            score += 50
        
        score += cluster.get('confidence', 0) * 10
        
        # Prefer clusters with canonical information
        if cluster.get('canonical_name'):
            score += 20
        if cluster.get('canonical_date'):
            score += 10
        
        return score
    
    # Sort by score (highest first)
    sorted_clusters = sorted(clusters, key=get_cluster_score, reverse=True)
    
    # Use the best cluster as base
    merged = sorted_clusters[0].copy()
    
    # Merge citations
    all_citations = []
    source_documents = set()
    
    for cluster in sorted_clusters:
        citations = cluster.get('citations', []) or cluster.get('citation_objects', [])
        if citations:
            all_citations.extend(citations)
        
        # Track source documents
        submitted_name = cluster.get('submitted_case_name') or cluster.get('extracted_case_name')
        submitted_date = cluster.get('submitted_date') or cluster.get('extracted_date')
        if submitted_name and submitted_date:
            source_documents.add((submitted_name, submitted_date))
    
    # Deduplicate citations based on text
    seen_citations = set()
    unique_citations = []
    
    for cit in all_citations:
        cit_text = cit.get('citation') or cit.get('text', '')
        if cit_text and cit_text not in seen_citations:
            seen_citations.add(cit_text)
            unique_citations.append(cit)
    
    merged['citations'] = unique_citations
    merged['citation_objects'] = unique_citations
    
    # Update source document information
    if source_documents:
        if len(source_documents) == 1:
            # Single source
            merged['submitted_case_name'], merged['submitted_date'] = source_documents.pop()
        else:
            # Multiple sources - create combined display
            names = [name for name, _ in source_documents]
            dates = [date for _, date in source_documents]
            merged['submitted_case_name'] = f"Multiple documents: {', '.join(names[:2])}"
            if len(names) > 2:
                merged['submitted_case_name'] += f" (+{len(names)-2} more)"
            merged['submitted_date'] = f"Multiple: {', '.join(set(dates[:2]))}"
            if len(set(dates)) > 2:
                merged['submitted_date'] += f" (+{len(set(dates))-2} more)"
    
    # Update cluster size
    merged['cluster_size'] = len(unique_citations)
    
    # Add flag indicating merge occurred
    merged['cross_document_merge'] = True
    merged['merge_source_count'] = len(clusters)
    
    return merged
