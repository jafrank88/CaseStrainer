#!/usr/bin/env python3
"""
Test script to verify Washington citation normalization (Wn. -> Wash.)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_washington_normalization():
    """Test that Washington citations are normalized from Wn. to Wash."""
    
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citations with Wn. format
    test_citations = [
        "123 Wn.2d 456",
        "456 Wn. App. 789",
        "789 Wn.2d 123, 321",
        "123 Wn. App. 456, 789",
    ]
    
    print("=" * 60)
    print("WASHINGTON CITATION NORMALIZATION TEST")
    print("=" * 60)
    print("Testing conversion from Wn. -> Wash.")
    print()
    
    for citation in test_citations:
        normalized = verifier._normalize_citation(citation)
        print(f"Original:  {citation}")
        print(f"Normalized: {normalized}")
        print("-" * 40)
    
    # Test that Wash. citations remain unchanged
    print("\n" + "=" * 60)
    print("TESTING THAT Wash. CITATIONS REMAIN UNCHANGED")
    print("=" * 60)
    
    wash_citations = [
        "123 Wash.2d 456",
        "456 Wash. App. 789",
        "789 Wash.2d 123, 321",
        "123 Wash. App. 456, 789",
    ]
    
    for citation in wash_citations:
        normalized = verifier._normalize_citation(citation)
        print(f"Original:  {citation}")
        print(f"Normalized: {normalized}")
        print("-" * 40)

if __name__ == "__main__":
    test_washington_normalization() 