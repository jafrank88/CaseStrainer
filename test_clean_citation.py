#!/usr/bin/env python3
"""
Test script to check the _clean_citation_for_lookup method.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_clean_citation():
    """Test the _clean_citation_for_lookup method."""
    
    print("=== TESTING _CLEAN_CITATION_FOR_LOOKUP ===")
    
    # Test citations
    test_citations = [
        "399 P.3d 1195",
        "199 Wn. App. 280",
        "399 P. 3d 1195"  # This is what we're seeing in the logs
    ]
    
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        verifier = EnhancedMultiSourceVerifier()
        print("✓ Created verifier instance")
        
        for citation in test_citations:
            print(f"\nTesting citation: '{citation}'")
            cleaned = verifier._clean_citation_for_lookup(citation)
            print(f"  Cleaned: '{cleaned}'")
            
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clean_citation() 