#!/usr/bin/env python3
"""
Simple test for parallel citation clustering logic.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CitationResult:
    """Structured result for a single citation."""
    citation: str
    case_name: Optional[str] = None
    context: str = ""
    start_index: Optional[int] = None
    end_index: Optional[int] = None
    is_parallel: bool = False
    parallel_citations: List[str] = None
    
    def __post_init__(self):
        if self.parallel_citations is None:
            self.parallel_citations = []

def calculate_context_similarity(context1: str, context2: str) -> float:
    """Calculate similarity between two context strings."""
    if not context1 or not context2:
        return 0.0
    
    # Simple Jaccard similarity on words
    words1 = set(context1.lower().split())
    words2 = set(context2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def calculate_case_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two case names."""
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
    
    # Get word sets
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def normalize_case_name(case_name: str) -> str:
    """Normalize case name for comparison."""
    if not case_name:
        return ""
    
    normalized = case_name.lower()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized

def group_parallel_citations(citations: List[CitationResult]) -> List[CitationResult]:
    """
    Group citations that are likely parallel citations for the same case.
    """
    if not citations:
        return citations
    
    # Sort by position in text for better grouping
    citations.sort(key=lambda x: getattr(x, 'start_index', 0))
    
    grouped = []
    processed = set()
    
    for i, citation in enumerate(citations):
        if i in processed:
            continue
        
        # Start a new group
        group = [citation]
        processed.add(i)
        
        # Look for citations that are explicitly together with this one
        for j, other in enumerate(citations):
            if j in processed:
                continue
            
            # Check for exact case name match first
            if (citation.case_name and other.case_name and 
                citation.case_name == other.case_name):
                
                # Check if they're in the same context block
                if citation.context and other.context:
                    
                    # Calculate context similarity
                    context_similarity = calculate_context_similarity(
                        citation.context, other.context
                    )
                    
                    if context_similarity > 0.6:
                        # Additional check: are they explicitly separated by punctuation?
                        combined_text = f"{citation.citation} {other.citation}"
                        if re.search(r'[,;]\s*', combined_text) or context_similarity > 0.7:
                            group.append(other)
                            processed.add(j)
                            continue
            
            # Check for very high similarity (0.85+) but only if they're in the same context
            elif (citation.case_name and other.case_name):
                similarity = calculate_case_name_similarity(
                    citation.case_name, other.case_name
                )
                
                if similarity >= 0.85:
                    # Additional requirement: they must be in the same context block
                    if citation.context and other.context:
                        
                        context_similarity = calculate_context_similarity(
                            citation.context, other.context
                        )
                        
                        if context_similarity > 0.5:
                            # Check for explicit grouping indicators
                            combined_context = f"{citation.context} {other.context}"
                            if re.search(r'[,;]\s*', combined_context):
                                group.append(other)
                                processed.add(j)
                                continue
        
        # If we have multiple citations in the group, create a combined result
        if len(group) > 1:
            # Use the first citation as primary and add others as parallel citations
            primary = group[0]
            primary.parallel_citations = [c.citation for c in group[1:]]
            primary.is_parallel = True
            grouped.append(primary)
        else:
            # Single citation, no grouping needed
            grouped.append(group[0])
    
    return grouped

def test_parallel_citation_clustering():
    """Test parallel citation clustering with various scenarios."""
    
    print("=== Testing Parallel Citation Clustering ===\n")
    
    # Test case 1: Multiple citations for the same case in same context
    citations_1 = [
        CitationResult(
            citation="123 F.3d 456",
            case_name="Smith v. Jones",
            context="In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), 456 F. Supp. 789 (D. Cal. 2020), the court held that parallel citations should be grouped together.",
            start_index=10
        ),
        CitationResult(
            citation="456 F. Supp. 789",
            case_name="Smith v. Jones",
            context="In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), 456 F. Supp. 789 (D. Cal. 2020), the court held that parallel citations should be grouped together.",
            start_index=50
        )
    ]
    
    print("Test 1: Same case name, multiple citations")
    grouped_1 = group_parallel_citations(citations_1)
    print(f"Input: {len(citations_1)} citations")
    print(f"Output: {len(grouped_1)} citations")
    
    for i, citation in enumerate(grouped_1):
        print(f"  Citation {i+1}: {citation.citation}")
        print(f"    Case name: {citation.case_name}")
        print(f"    Parallel citations: {citation.parallel_citations}")
        print(f"    Is parallel: {citation.is_parallel}")
    print()
    
    # Test case 2: Different cases (should not be grouped)
    citations_2 = [
        CitationResult(
            citation="123 F.3d 456",
            case_name="Smith v. Jones",
            context="In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court held one thing.",
            start_index=10
        ),
        CitationResult(
            citation="456 F.3d 789",
            case_name="Johnson v. Smith",
            context="In Johnson v. Smith, 456 F.3d 789 (8th Cir. 2021), the court held another.",
            start_index=50
        )
    ]
    
    print("Test 2: Different cases (should not be grouped)")
    grouped_2 = group_parallel_citations(citations_2)
    print(f"Input: {len(citations_2)} citations")
    print(f"Output: {len(grouped_2)} citations")
    
    for i, citation in enumerate(grouped_2):
        print(f"  Citation {i+1}: {citation.citation}")
        print(f"    Case name: {citation.case_name}")
        print(f"    Parallel citations: {citation.parallel_citations}")
        print(f"    Is parallel: {citation.is_parallel}")
    print()
    
    # Test case 3: Complex parallel citation pattern
    citations_3 = [
        CitationResult(
            citation="384 U.S. 436",
            case_name="Miranda v. Arizona",
            context="The landmark case of Miranda v. Arizona, 384 U.S. 436 (1966), 86 S. Ct. 1602, 16 L. Ed. 2d 694, 10 A.L.R.3d 974, established the Miranda rights.",
            start_index=30
        ),
        CitationResult(
            citation="86 S. Ct. 1602",
            case_name="Miranda v. Arizona",
            context="The landmark case of Miranda v. Arizona, 384 U.S. 436 (1966), 86 S. Ct. 1602, 16 L. Ed. 2d 694, 10 A.L.R.3d 974, established the Miranda rights.",
            start_index=50
        ),
        CitationResult(
            citation="16 L. Ed. 2d 694",
            case_name="Miranda v. Arizona",
            context="The landmark case of Miranda v. Arizona, 384 U.S. 436 (1966), 86 S. Ct. 1602, 16 L. Ed. 2d 694, 10 A.L.R.3d 974, established the Miranda rights.",
            start_index=70
        )
    ]
    
    print("Test 3: Complex parallel citation pattern")
    grouped_3 = group_parallel_citations(citations_3)
    print(f"Input: {len(citations_3)} citations")
    print(f"Output: {len(grouped_3)} citations")
    
    for i, citation in enumerate(grouped_3):
        print(f"  Citation {i+1}: {citation.citation}")
        print(f"    Case name: {citation.case_name}")
        print(f"    Parallel citations: {citation.parallel_citations}")
        print(f"    Is parallel: {citation.is_parallel}")
    print()

if __name__ == "__main__":
    test_parallel_citation_clustering() 