#!/usr/bin/env python3
"""
Test script to trace citation processing and find where it's being converted to lowercase.
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_citation_processing():
    """Test citation processing step by step to find where lowercase conversion happens."""
    
    print("=== TESTING CITATION PROCESSING STEP BY STEP ===")
    
    # Test citation
    original_citation = "199 Wn. App. 280"
    print(f"Original citation: '{original_citation}'")
    
    try:
        from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        from src.citation_format_utils import normalize_washington_synonyms
        
        verifier = EnhancedMultiSourceVerifier()
        print("✓ Created verifier instance")
        
        # Test 1: Check normalization
        print(f"\n1. After normalize_washington_synonyms: '{normalize_washington_synonyms(original_citation)}'")
        
        # Test 2: Check _clean_citation_for_lookup
        cleaned = verifier._clean_citation_for_lookup(original_citation)
        print(f"2. After _clean_citation_for_lookup: '{cleaned}'")
        
        # Test 3: Check _extract_citation_components
        components = verifier._extract_citation_components(original_citation)
        print(f"3. After _extract_citation_components:")
        print(f"   Volume: '{components.get('volume', 'N/A')}'")
        print(f"   Reporter: '{components.get('reporter', 'N/A')}'")
        print(f"   Page: '{components.get('page', 'N/A')}'")
        print(f"   Court: '{components.get('court', 'N/A')}'")
        
        # Test 4: Check what happens in verify_citation_unified_workflow
        print(f"\n4. Testing verify_citation_unified_workflow...")
        result = verifier.verify_citation_unified_workflow(original_citation)
        print(f"   Result citation: '{result.get('citation', 'N/A')}'")
        print(f"   Canonical citation: '{result.get('canonical_citation', 'N/A')}'")
        print(f"   Verified: {result.get('verified', 'N/A')}")
        print(f"   Source: '{result.get('source', 'N/A')}'")
        
        # Test 5: Check what happens in _verify_with_courtlistener
        print(f"\n5. Testing _verify_with_courtlistener...")
        courtlistener_result = verifier._verify_with_courtlistener(original_citation)
        print(f"   Result citation: '{courtlistener_result.get('citation', 'N/A')}'")
        print(f"   Verified: {courtlistener_result.get('verified', 'N/A')}")
        print(f"   Source: '{courtlistener_result.get('source', 'N/A')}'")
        
        # Test 6: Check what happens in _lookup_citation
        print(f"\n6. Testing _lookup_citation...")
        lookup_result = verifier._lookup_citation(original_citation)
        if lookup_result:
            print(f"   Result citation: '{lookup_result.get('citation', 'N/A')}'")
            print(f"   Verified: {lookup_result.get('verified', 'N/A')}")
            print(f"   Source: '{lookup_result.get('source', 'N/A')}'")
        else:
            print("   Result: None")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_citation_processing() 