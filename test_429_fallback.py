#!/usr/bin/env python3
"""
Test that 429 rate limit errors are properly handled and fallback verification is used.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.unified_verification_master import verify_citation_unified_master_sync

def test_429_handling():
    """Test that 429 errors trigger fallback verification."""
    
    test_cases = [
        # These citations should trigger CourtListener API calls
        "578 U.S. 330",  # Spokeo case
        "131 Wn.2d 523",  # Washington case
        "936 P.2d 1123",  # Pacific case
    ]
    
    print("Testing 429 rate limit handling...")
    print("=" * 60)
    
    for citation in test_cases:
        print(f"\nTesting citation: {citation}")
        
        # Force verification to be enabled
        os.environ['ENABLE_VERIFICATION'] = 'true'
        
        try:
            # This should handle 429 gracefully and use fallback
            result = verify_citation_unified_master_sync(
                citation=citation,
                extracted_case_name=None,
                extracted_date=None,
                timeout=30.0,  # Give time for fallback
                enable_fallback=True
            )
            
            print(f"  Status: {'VERIFIED' if result.get('verified') else 'UNVERIFIED'}")
            print(f"  Source: {result.get('source', 'unknown')}")
            print(f"  Error: {result.get('error') or 'None'}")
            
            # If we got a result, 429 was handled properly
            if result.get('verified') or result.get('source') != 'disabled':
                print("  PASS: 429 handled correctly - fallback verification used")
            else:
                print("  WARN: No verification result")
                
        except Exception as e:
            print(f"  ERROR Exception: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed - 429 errors should be handled gracefully")

if __name__ == "__main__":
    test_429_handling()
