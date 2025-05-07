#!/usr/bin/env python3
"""
Citation Grouping Module for CaseStrainer

This module provides functionality to group multiple citations that refer to the same case.
"""

import re
from typing import List, Dict, Any, Set, Tuple


def normalize_case_name(case_name: str) -> str:
    """
    Normalize a case name for comparison purposes.
    
    Args:
        case_name: The case name to normalize
        
    Returns:
        Normalized case name
    """
    if not case_name:
        return ""
    
    # Convert to lowercase
    normalized = case_name.lower()
    
    # Remove common prefixes
    prefixes = ["in re ", "state v. ", "state of washington v. "]
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    
    # Remove punctuation and extra spaces
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def calculate_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two case names.
    
    Args:
        name1: First case name
        name2: Second case name
        
    Returns:
        Similarity score between 0 and 1
    """
    if not name1 or not name2:
        return 0.0
    
    # Normalize names
    norm1 = normalize_case_name(name1)
    norm2 = normalize_case_name(name2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Check for exact match
    if norm1 == norm2:
        return 1.0
    
    # Check for one name being a substring of the other
    if norm1 in norm2 or norm2 in norm1:
        return 0.8
    
    # Calculate word overlap
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0


def group_citations_by_case(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group multiple citations that refer to the same case.
    
    Args:
        citations: List of citation dictionaries, each with 'citation', 'case_name', etc.
        
    Returns:
        List of grouped citation dictionaries with additional 'alternate_citations' field
    """
    if not citations:
        return []
    
    # Group by case name similarity
    grouped_citations = []
    processed_indices = set()
    
    for i, citation in enumerate(citations):
        if i in processed_indices:
            continue
        
        case_name = citation.get('case_name', '')
        
        # If no case name or unknown case, can't group, so add as is
        if not case_name or case_name == 'Unknown case' or case_name.lower() == 'unknown case':
            citation_copy = citation.copy()
            citation_copy['alternate_citations'] = []
            grouped_citations.append(citation_copy)
            processed_indices.add(i)
            continue
        
        # Create a new group with this citation as the primary
        group = citation.copy()
        group['alternate_citations'] = []
        processed_indices.add(i)
        
        # Find similar case names
        for j, other in enumerate(citations):
            if j in processed_indices:
                continue
            
            other_case_name = other.get('case_name', '')
            
            # Skip citations with unknown case names - they should never be grouped
            if not other_case_name or other_case_name == 'Unknown case' or other_case_name.lower() == 'unknown case':
                continue
            
            similarity = calculate_similarity(case_name, other_case_name)
            if similarity >= 0.7:  # Threshold for considering same case
                # Add as alternate citation
                group['alternate_citations'].append({
                    'citation': other.get('citation', ''),
                    'case_name': other.get('case_name', ''),
                    'url': other.get('url', ''),
                    'source': other.get('source', ''),
                    'similarity': similarity
                })
                processed_indices.add(j)
        
        grouped_citations.append(group)
    
    return grouped_citations


def group_citations_by_url(citations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Group multiple citations that have the same URL.
    
    Args:
        citations: List of citation dictionaries, each with 'citation', 'url', etc.
        
    Returns:
        List of grouped citation dictionaries with additional 'alternate_citations' field
    """
    if not citations:
        return []
    
    # Group by URL
    url_groups: Dict[str, List[int]] = {}
    
    for i, citation in enumerate(citations):
        url = citation.get('url', '')
        case_name = citation.get('case_name', '')
        
        # Skip citations with unknown case names - they should never be grouped
        if not case_name or case_name == 'Unknown case' or case_name.lower() == 'unknown case':
            continue
            
        if url:
            if url not in url_groups:
                url_groups[url] = []
            url_groups[url].append(i)
    
    # Create grouped citations
    grouped_citations = []
    processed_indices = set()
    
    # First process URL groups
    for url, indices in url_groups.items():
        if len(indices) <= 1:
            # Skip groups with only one citation (will be handled later)
            continue
        
        # Use the first citation as the primary
        primary_idx = indices[0]
        primary = citations[primary_idx].copy()
        primary['alternate_citations'] = []
        processed_indices.add(primary_idx)
        
        # Add the rest as alternates
        for idx in indices[1:]:
            other = citations[idx]
            # Double-check that we're not grouping unknown case names
            other_case_name = other.get('case_name', '')
            if not other_case_name or other_case_name == 'Unknown case' or other_case_name.lower() == 'unknown case':
                continue
                
            primary['alternate_citations'].append({
                'citation': other.get('citation', ''),
                'case_name': other.get('case_name', ''),
                'url': other.get('url', ''),
                'source': other.get('source', '')
            })
            processed_indices.add(idx)
        
        grouped_citations.append(primary)
    
    # Add any remaining citations that weren't grouped by URL
    for i, citation in enumerate(citations):
        if i not in processed_indices:
            citation_copy = citation.copy()
            citation_copy['alternate_citations'] = []
            grouped_citations.append(citation_copy)
    
    return grouped_citations


def group_citations(citations: List[Dict[str, Any]], method: str = 'url_then_name') -> List[Dict[str, Any]]:
    """
    Group multiple citations that refer to the same case using the specified method.
    
    Args:
        citations: List of citation dictionaries
        method: Grouping method ('url', 'name', or 'url_then_name')
        
    Returns:
        List of grouped citation dictionaries
    """
    if not citations:
        return []
    
    if method == 'url':
        return group_citations_by_url(citations)
    elif method == 'name':
        return group_citations_by_case(citations)
    elif method == 'url_then_name':
        # First group by URL
        url_grouped = group_citations_by_url(citations)
        # Then group by case name
        return group_citations_by_case(url_grouped)
    else:
        # Default to URL grouping if invalid method
        return group_citations_by_url(citations)


if __name__ == "__main__":
    # Example usage
    test_citations = [
        {
            'citation': '410 U.S. 113',
            'case_name': 'Roe v. Wade',
            'url': 'https://www.courtlistener.com/opinion/108713/roe-v-wade/',
            'source': 'CourtListener Citation API'
        },
        {
            'citation': '93 S. Ct. 705',
            'case_name': 'Roe v. Wade',
            'url': 'https://www.courtlistener.com/opinion/108713/roe-v-wade/',
            'source': 'CourtListener Citation API'
        },
        {
            'citation': '35 L. Ed. 2d 147',
            'case_name': 'Roe against Wade',
            'url': 'https://www.courtlistener.com/opinion/108713/roe-v-wade/',
            'source': 'CourtListener Citation API'
        },
        {
            'citation': '196 Wash. 2d 725',
            'case_name': 'Associated Press v. Washington State Legislature',
            'url': 'https://www.courtlistener.com/opinion/4688692/associated-press-v-wash-state-legislature/',
            'source': 'CourtListener Search API'
        },
        {
            'citation': '455 P.3d 1164',
            'case_name': 'Associated Press v. Wash. State Legislature',
            'url': 'https://www.courtlistener.com/opinion/4688692/associated-press-v-wash-state-legislature/',
            'source': 'CourtListener Search API'
        }
    ]
    
    grouped = group_citations(test_citations)
    
    print(f"\nGrouped {len(test_citations)} citations into {len(grouped)} groups:")
    for i, group in enumerate(grouped):
        print(f"\nGroup {i+1}:")
        print(f"  Primary Citation: {group['citation']}")
        print(f"  Case Name: {group['case_name']}")
        print(f"  URL: {group['url']}")
        print(f"  Source: {group['source']}")
        
        if group.get('alternate_citations'):
            print(f"  Alternate Citations ({len(group['alternate_citations'])}):")  
            for alt in group['alternate_citations']:
                print(f"    - {alt['citation']} ({alt['source']})")
    
    import json
    with open('grouped_citations.json', 'w', encoding='utf-8') as f:
        json.dump(grouped, f, indent=2)
    print("\nResults saved to grouped_citations.json")
