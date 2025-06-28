#!/usr/bin/env python3
"""
Test script to verify Washington citation lookup and verification.
"""
import os
import sys
sys.path.append('src')

from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_washington_citations():
    """Test Washington citation verification."""
    
    # Test Washington citations
    test_citations = [
        "97 Wash. 2d 30",
        "185 Wash. 2d 363", 
        "190 Wash. 2d 185",
        "121 Wash. 2d 205",
        "177 Wash. 2d 351"
    ]
    
    print("Testing Washington Citation Verification")
    print("=" * 50)
    
    verifier = EnhancedMultiSourceVerifier()
    
    for i, citation in enumerate(test_citations, 1):
        print(f"\n{i}. Testing: {citation}")
        print("-" * 30)
        
        try:
            result = verifier.verify_citation_unified_workflow(citation)
            
            print(f"  Verified: {result.get('verified')}")
            print(f"  Case Name: {result.get('case_name')}")
            print(f"  Canonical Name: {result.get('canonical_name')}")
            print(f"  URL: {result.get('url')}")
            print(f"  Court: {result.get('court')}")
            print(f"  Source: {result.get('source')}")
            print(f"  Method: {result.get('verification_method')}")
            print(f"  Error: {result.get('error')}")
            
            if result.get('verified') == 'true':
                print(f"  ✅ SUCCESS: Citation verified!")
            else:
                print(f"  ❌ FAILED: Citation not verified")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    print(f"\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_washington_citations() 