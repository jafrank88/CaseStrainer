#!/usr/bin/env python3
"""
Test script to debug the backend citation verification for Black and Knight citations.
This will help us identify and fix the issues with source, canonical case, and fallback methods.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_courtlistener_verification import EnhancedCourtListenerVerifier
from enhanced_fallback_verifier import EnhancedFallbackVerifier

async def test_courtlistener_verification():
    """Test the CourtListener verification directly."""
    print("=" * 80)
    print("TESTING COURTLISTENER VERIFICATION")
    print("=" * 80)
    
    # Get API key from environment or use a placeholder for testing
    api_key = os.getenv('COURTLISTENER_API_KEY', 'test_key_for_debugging')
    verifier = EnhancedCourtListenerVerifier(api_key)
    
    # Test the specific citations from the paragraph
    test_citations = [
        "178 Wn. App. 929",  # Knight case
        "317 P.3d 1068",     # Knight case  
        "188 Wn.2d 114",     # Black case
        "392 P.3d 1041",     # Black case
        "155 Wn. App. 715",  # Blackmon case
        "230 P.3d 233"       # Blackmon case
    ]
    
    for citation in test_citations:
        print(f"\n--- Testing Citation: {citation} ---")
        try:
            result = verifier.verify_citation_enhanced(citation)
            print(f"Result: {result}")
            
            if result.get('verified'):
                print(f"✅ VERIFIED: {result.get('canonical_name')} ({result.get('canonical_date')})")
                print(f"   Source: {result.get('source')}")
                print(f"   URL: {result.get('canonical_url')}")
            else:
                print(f"❌ NOT VERIFIED: {result.get('error_message', 'No error message')}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

async def test_fallback_verifier():
    """Test the enhanced fallback verifier directly."""
    print("\n" + "=" * 80)
    print("TESTING ENHANCED FALLBACK VERIFIER")
    print("=" * 80)
    
    verifier = EnhancedFallbackVerifier()
    
    # Test the specific citations from the paragraph
    test_citations = [
        "178 Wn. App. 929",  # Knight case
        "317 P.3d 1068",     # Knight case  
        "188 Wn.2d 114",     # Black case
        "392 P.3d 1041",     # Black case
        "155 Wn. App. 715",  # Blackmon case
        "230 P.3d 233"       # Blackmon case
    ]
    
    for citation in test_citations:
        print(f"\n--- Testing Citation: {citation} ---")
        try:
            result = await verifier.verify_citation(citation)
            print(f"Result: {result}")
            
            if result.get('verified'):
                print(f"✅ VERIFIED: {result.get('canonical_name')} ({result.get('canonical_date')})")
                print(f"   Source: {result.get('source')}")
                print(f"   URL: {result.get('canonical_url')}")
                print(f"   Confidence: {result.get('confidence')}")
            else:
                print(f"❌ NOT VERIFIED: {result.get('error_message', 'No error message')}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

async def test_batch_verification():
    """Test batch verification to see if it works better."""
    print("\n" + "=" * 80)
    print("TESTING BATCH VERIFICATION")
    print("=" * 80)
    
    # Get API key from environment or use a placeholder for testing
    api_key = os.getenv('COURTLISTENER_API_KEY', 'test_key_for_debugging')
    verifier = EnhancedCourtListenerVerifier(api_key)
    
    # Test batch verification
    test_citations = [
        "178 Wn. App. 929",  # Knight case
        "317 P.3d 1068",     # Knight case  
        "188 Wn.2d 114",     # Black case
        "392 P.3d 1041",     # Black case
    ]
    
    try:
        results = verifier.verify_citations_batch(test_citations)
        print(f"Batch Results: {results}")
        
        for i, result in enumerate(results):
            citation = test_citations[i]
            if result.get('verified'):
                print(f"✅ {citation}: {result.get('canonical_name')} ({result.get('canonical_date')})")
                print(f"   Source: {result.get('source')}")
                print(f"   URL: {result.get('canonical_url')}")
            else:
                print(f"❌ {citation}: {result.get('error_message', 'No error message')}")
                
    except Exception as e:
        print(f"❌ BATCH ERROR: {e}")
        import traceback
        traceback.print_exc()

def test_citation_matching():
    """Test the citation matching logic directly."""
    print("\n" + "=" * 80)
    print("TESTING CITATION MATCHING LOGIC")
    print("=" * 80)
    
    # Get API key from environment or use a placeholder for testing
    api_key = os.getenv('COURTLISTENER_API_KEY', 'test_key_for_debugging')
    verifier = EnhancedCourtListenerVerifier(api_key)
    
    # Test specific citation pairs that should match
    test_pairs = [
        ("178 Wn. App. 929", "178 Wash. App. 929"),  # Should match
        ("317 P.3d 1068", "317 P.3d 1068"),         # Should match
        ("188 Wn.2d 114", "188 Wash. 2d 114"),       # Should match
        ("392 P.3d 1041", "392 P.3d 1041"),         # Should match
    ]
    
    for citation1, citation2 in test_pairs:
        try:
            match = verifier._citations_match(citation1, citation2)
            print(f"'{citation1}' vs '{citation2}': {'✅ MATCH' if match else '❌ NO MATCH'}")
        except Exception as e:
            print(f"'{citation1}' vs '{citation2}': ❌ ERROR - {e}")

async def main():
    """Run all tests."""
    print("Starting comprehensive backend testing for Black and Knight citations...")
    
    # Test citation matching logic first
    test_citation_matching()
    
    # Test CourtListener verification
    await test_courtlistener_verification()
    
    # Test batch verification
    await test_batch_verification()
    
    # Test enhanced fallback verifier
    await test_fallback_verifier()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
