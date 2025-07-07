#!/usr/bin/env python3
"""
Test script to demonstrate and fix the Washington citation normalization issue.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_washington_normalization():
    """Test Washington citation normalization."""
    
    print("=== TESTING WASHINGTON CITATION NORMALIZATION ===")
    
    # Test citation
    test_citation = "115 Wn.2d 294"
    print(f"Original citation: '{test_citation}'")
    
    try:
        # Test the normalization functions
        from src.citation_format_utils import normalize_washington_synonyms
        from src.citation_normalizer import normalize_citation
        from src.citation_extractor import normalize_washington_citations
        
        print(f"\n1. normalize_washington_synonyms: '{normalize_washington_synonyms(test_citation)}'")
        print(f"2. normalize_citation: '{normalize_citation(test_citation)}'")
        print(f"3. normalize_washington_citations: '{normalize_washington_citations(test_citation)}'")
        
        # Test the verifier without normalization
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        verifier = EnhancedMultiSourceVerifier()
        
        print(f"\n4. extract_clean_citation (no normalization): '{verifier.extract_clean_citation(test_citation)}'")
        
        # Test what happens in the actual workflow
        print(f"\n5. Testing verify_citation_unified_workflow...")
        result = verifier.verify_citation_unified_workflow(test_citation)
        print(f"   Result citation: '{result.get('canonical_citation', 'N/A')}'")
        print(f"   Verified: {result.get('verified', False)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_washington_normalization() 