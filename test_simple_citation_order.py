#!/usr/bin/env python3
"""
Simple test script to verify citation extraction and ordering without verification.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from unified_citation_processor import UnifiedCitationProcessor

def test_simple_citation_order():
    """Test citation extraction and ordering without verification."""
    
    # Test text with citations in specific order
    test_text = """
    This document discusses several important cases.
    
    First, we have Brown v. Board of Education, 347 U.S. 483 (1954).
    
    Then we discuss Miranda v. Arizona, 384 U.S. 436 (1966).
    
    Finally, we examine Roe v. Wade, 410 U.S. 113 (1973).
    
    We also reference Gideon v. Wainwright, 372 U.S. 335 (1963) in passing.
    """
    
    print("Testing simple citation extraction and ordering...")
    print("Test text:")
    print(test_text)
    print("-" * 80)
    
    # Process the text
    processor = UnifiedCitationProcessor()
    
    # Just extract citations without verification
    citations = processor.extract_citations(test_text)
    
    print("Extracted citations in order:")
    for i, citation in enumerate(citations, 1):
        print(f"{i}. {citation.citation} (position: {citation.start_index})")
    
    print("-" * 80)
    
    # Verify order by checking if positions are increasing
    positions = []
    for citation in citations:
        if citation.start_index is not None:
            positions.append(citation.start_index)
    
    if len(positions) > 1:
        is_ordered = all(positions[i] <= positions[i+1] for i in range(len(positions)-1))
        print(f"Citations are in document order: {is_ordered}")
        
        if not is_ordered:
            print("WARNING: Citations are not in document order!")
            print("Positions:", positions)
    else:
        print("Not enough citations with position data to verify order")
    
    return citations

if __name__ == "__main__":
    test_simple_citation_order() 