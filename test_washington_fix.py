#!/usr/bin/env python3
"""
Test script to verify the Washington citation normalization fix.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_washington_fix():
    """Test the Washington citation normalization fix."""
    
    print("=== TESTING WASHINGTON CITATION NORMALIZATION FIX ===")
    
    # Test citation
    test_citation = "115 Wn.2d 294"
    print(f"Original citation: '{test_citation}'")
    
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        verifier = EnhancedMultiSourceVerifier()
        
        # Test the normalization method directly
        normalized = verifier._normalize_washington_citation(test_citation)
        print(f"Normalized citation: '{normalized}'")
        
        # Test extract_clean_citation
        clean_citation = verifier.extract_clean_citation(test_citation)
        print(f"Clean citation: '{clean_citation}'")
        
        # Test the full workflow
        print(f"\nTesting full workflow...")
        result = verifier.verify_citation_unified_workflow(test_citation)
        print(f"Workflow result citation: '{result.get('canonical_citation', 'N/A')}'")
        print(f"Verified: {result.get('verified', False)}")
        
        # Test other Washington citations
        test_cases = [
            "115 Wn.2d 294",
            "115 Wn. 2d 294", 
            "115 Wn.3d 456",
            "45 Wn. App. 678",
            "45 Wn.App. 678"
        ]
        
        print(f"\n=== TESTING VARIOUS WASHINGTON FORMATS ===")
        for case in test_cases:
            normalized = verifier._normalize_washington_citation(case)
            print(f"'{case}' -> '{normalized}'")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_washington_fix() 