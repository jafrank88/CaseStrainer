#!/usr/bin/env python3
"""
Test script to test parallel citation handling with the exact citation provided.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_parallel_citation():
    """Test parallel citation handling."""
    
    print("=== TESTING PARALLEL CITATION HANDLING ===")
    
    # Test text - exact citation from user
    test_text = "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    print(f"Test text: '{test_text}'")
    
    try:
        from src.complex_citation_integration import process_text_with_complex_citations
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        verifier = EnhancedMultiSourceVerifier()
        print("✓ Created verifier instance")
        
        # Test the process_text_with_complex_citations function
        print("Testing process_text_with_complex_citations...")
        results = process_text_with_complex_citations(test_text, verifier)
        
        print(f"Got {len(results)} results:")
        for i, result in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print(f"Citation: {result.get('citation', 'N/A')}")
            print(f"Verified: {result.get('verified', 'N/A')}")
            print(f"Valid: {result.get('valid', 'N/A')}")
            print(f"Source: {result.get('source', 'N/A')}")
            print(f"URL: {result.get('url', 'N/A')}")
            print(f"Court: {result.get('court', 'N/A')}")
            print(f"Docket: {result.get('docket_number', 'N/A')}")
            print(f"Case name: {result.get('case_name', 'N/A')}")
            print(f"Canonical name: {result.get('canonical_name', 'N/A')}")
            print(f"Is parallel: {result.get('is_parallel_citation', False)}")
            print(f"Primary citation: {result.get('primary_citation', 'N/A')}")
            
            # Check if metadata was copied from primary
            if result.get('is_parallel_citation'):
                print("  ✓ This is a parallel citation")
                if result.get('url'):
                    print("  ✓ Has URL (copied from primary)")
                if result.get('case_name'):
                    print("  ✓ Has case name (copied from primary)")
                else:
                    print("  ✗ Missing case name (should be copied from primary)")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parallel_citation() 