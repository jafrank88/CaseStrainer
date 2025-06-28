#!/usr/bin/env python3
"""
Simple test to verify CourtListener API is working correctly.
"""
import os
import sys
sys.path.append('src')

from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_courtlistener_verification():
    """Test CourtListener verification with a known good citation."""
    
    # Test with a known good citation
    test_citation = "534 F.3d 1290"
    
    print(f"Testing CourtListener verification for: {test_citation}")
    
    try:
        verifier = EnhancedMultiSourceVerifier()
        result = verifier.verify_citation_unified_workflow(test_citation)
        
        print(f"\nResult:")
        print(f"  Verified: {result.get('verified')}")
        print(f"  Case Name: {result.get('case_name')}")
        print(f"  Canonical Name: {result.get('canonical_name')}")
        print(f"  URL: {result.get('url')}")
        print(f"  Source: {result.get('source')}")
        print(f"  Error: {result.get('error')}")
        
        if result.get('verified') == 'true':
            print(f"  ✅ SUCCESS: Citation verified successfully")
        else:
            print(f"  ❌ FAILED: Citation not verified")
            
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_courtlistener_verification() 