#!/usr/bin/env python3
"""
Test script to verify citation 399 P.3d 1195 using the enhanced multi-source verifier.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_citation_verification():
    """Test the citation verification for 399 P.3d 1195."""
    
    print("Testing Enhanced Multi-Source Citation Verification")
    print("=" * 60)
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citation
    citation = "399 P.3d 1195"
    case_name = "Doe v. Thurston County"
    
    print(f"Citation: {citation}")
    print(f"Case Name: {case_name}")
    print("-" * 60)
    
    # Test API verification (this will try multiple sources)
    print("Testing API verification (multiple sources)...")
    api_result = verifier._verify_with_api(citation)
    
    print(f"API Result:")
    print(f"  Verified: {api_result.get('verified', False)}")
    print(f"  Source: {api_result.get('source', 'Unknown')}")
    print(f"  Case Name: {api_result.get('case_name', 'N/A')}")
    print(f"  URL: {api_result.get('url', 'N/A')}")
    if api_result.get('error'):
        print(f"  Error: {api_result.get('error')}")
    if api_result.get('details'):
        print(f"  Details: {api_result.get('details')}")
    
    print("-" * 60)
    
    # Test individual sources
    sources = [
        ("Google Scholar", verifier._try_google_scholar),
        ("Justia", verifier._try_justia),
        ("Leagle", verifier._try_leagle),
        ("FindLaw", verifier._try_findlaw),
        ("CaseText", verifier._try_casetext),
    ]
    
    print("Testing individual sources:")
    for source_name, verify_method in sources:
        try:
            result = verify_method(citation)
            status = "✓ FOUND" if result.get('verified', False) else "✗ NOT FOUND"
            print(f"  {source_name}: {status}")
            if result.get('verified', False):
                print(f"    URL: {result.get('url', 'N/A')}")
        except Exception as e:
            print(f"  {source_name}: ERROR - {e}")
    
    print("-" * 60)
    
    # Test full verification process
    print("Testing full verification process...")
    full_result = verifier.verify_citation(citation, use_api=True, use_cache=False)
    
    print(f"Full Result:")
    print(f"  Verified: {full_result.get('verified', False)}")
    print(f"  Source: {full_result.get('source', 'Unknown')}")
    print(f"  Case Name: {full_result.get('case_name', 'N/A')}")
    print(f"  URL: {full_result.get('url', 'N/A')}")
    if full_result.get('error'):
        print(f"  Error: {full_result.get('error')}")
    
    print("=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_citation_verification()
