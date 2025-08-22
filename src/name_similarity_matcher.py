#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Name similarity matching utility for selecting the best CourtListener result
when multiple cases are returned for the same citation.
"""

import os
import re
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional

def normalize_case_name(name: str) -> str:
    """Normalize a case name for similarity comparison."""
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove common legal abbreviations and punctuation
    name = re.sub(r'\b(inc|corp|ltd|llc|co|assoc|bros|dr|jr|sr|st|mt|ft|univ|nat\'l|fed|comm\'n|bd|ctr|dept|hosp)\b\.?', '', name)
    
    # Remove extra whitespace and punctuation
    name = re.sub(r'[^\w\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()

def calculate_case_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two case names using multiple methods."""
    if not name1 or not name2:
        return 0.0
    
    # Normalize both names
    norm1 = normalize_case_name(name1)
    norm2 = normalize_case_name(name2)
    
    if not norm1 or not norm2:
        return 0.0
    
    # Method 1: Sequence matcher (overall similarity)
    seq_similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Method 2: Word-based similarity (handles reordering)
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if len(words1) == 0 and len(words2) == 0:
        word_similarity = 1.0
    elif len(words1) == 0 or len(words2) == 0:
        word_similarity = 0.0
    else:
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        word_similarity = intersection / union if union > 0 else 0.0
    
    # Method 3: Substring matching (handles partial matches)
    substring_similarity = 0.0
    if norm1 in norm2 or norm2 in norm1:
        substring_similarity = min(len(norm1), len(norm2)) / max(len(norm1), len(norm2))
    
    # Combine methods with weights
    combined_similarity = (
        0.4 * seq_similarity +
        0.4 * word_similarity +
        0.2 * substring_similarity
    )
    
    return combined_similarity

def select_best_courtlistener_result(
    results: List[Dict[str, Any]], 
    extracted_case_name: str,
    debug: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Select the best CourtListener result based on case name similarity.
    
    Args:
        results: List of CourtListener API results
        extracted_case_name: The case name extracted from the citation text
        debug: Whether to print debug information
        
    Returns:
        The best matching result, or the first result if no good match is found
    """
    if not results:
        return None
    
    if len(results) == 1:
        return results[0]
    
    if not extracted_case_name:
        if debug:
            print("[DEBUG] No extracted case name provided, returning first result")
        return results[0]
    
    best_result = None
    best_similarity = 0.0
    
    if debug:
        print(f"[DEBUG] Comparing {len(results)} CourtListener results to extracted name: '{extracted_case_name}'")
    
    for i, result in enumerate(results):
        # Extract case name from result
        case_name = None
        
        # Try to get case name from clusters first
        clusters = result.get('clusters', [])
        if clusters and len(clusters) > 0:
            case_name = clusters[0].get('case_name')
        
        # Fallback to other possible fields (including canonical_name)
        if not case_name:
            case_name = (result.get('canonical_name') or 
                        result.get('case_name') or 
                        result.get('caseName') or 
                        result.get('name'))
        
        if not case_name:
            if debug:
                print(f"[DEBUG] Result {i+1}: No case name found, skipping")
            continue
        
        # Calculate similarity
        similarity = calculate_case_name_similarity(extracted_case_name, case_name)
        
        if debug:
            print(f"[DEBUG] Result {i+1}: '{case_name}' - Similarity: {similarity:.3f}")
        
        # Update best result if this is better
        if similarity > best_similarity:
            best_similarity = similarity
            best_result = result
    
    # Use a threshold to determine if we found a good match
    similarity_threshold = 0.3  # Adjust as needed
    
    if best_result and best_similarity >= similarity_threshold:
        if debug:
            print(f"[DEBUG] Selected result with similarity {best_similarity:.3f} (above threshold {similarity_threshold})")
        return best_result
    else:
        if debug:
            print(f"[DEBUG] No result above similarity threshold {similarity_threshold}, returning first result")
        return results[0]

def test_name_similarity():
    """Test the name similarity matching with Luis v. United States example."""
    
    # Test case names
    extracted_name = "Luis v. United States"
    
    test_cases = [
        "Friedrichs v. Cal. Teachers Ass'n",
        "Luis v. United States", 
        "United States v. Luis",
        "Luis v. U.S.",
        "Friedrichs v. California Teachers Association"
    ]
    
    print("Testing name similarity matching:")
    print(f"Extracted name: '{extracted_name}'")
    print()
    
    for case_name in test_cases:
        similarity = calculate_case_name_similarity(extracted_name, case_name)
        print(f"'{case_name}' - Similarity: {similarity:.3f}")
    
    print()
    
    # Test with mock CourtListener results
    mock_results = [
        {
            'clusters': [{'case_name': 'Friedrichs v. Cal. Teachers Ass\'n'}]
        },
        {
            'clusters': [{'case_name': 'Luis v. United States'}]
        }
    ]
    
    best_result = select_best_courtlistener_result(mock_results, extracted_name, debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")
    if best_result:
        best_case_name = best_result['clusters'][0]['case_name']
        print(f"\nBest result: '{best_case_name}'")

if __name__ == '__main__':
    test_name_similarity()
