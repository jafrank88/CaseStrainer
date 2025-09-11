#!/usr/bin/env python3
"""
Test script to debug the enhanced verification system directly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_courtlistener_verification import EnhancedCourtListenerVerifier

def test_enhanced_verification():
    """Test the enhanced verification directly."""
    
    # Get API key from environment
    api_key = os.getenv('COURTLISTENER_API_KEY', 'test_key_for_debugging')
    verifier = EnhancedCourtListenerVerifier(api_key)
    
    # Test the specific problematic citations
    test_cases = [
        {
            'citation': '317 P.3d 1068',
            'extracted_case_name': 'In re Vulnerable Adult Petition for Knight',
            'expected': 'In re Vulnerable Adult Petition for Knight'
        },
        {
            'citation': '178 Wn. App. 929',
            'extracted_case_name': 'In re Vulnerable Adult Petition for Knight',
            'expected': 'In re Vulnerable Adult Petition for Knight'
        },
        {
            'citation': '188 Wn.2d 114',
            'extracted_case_name': 'In re Marriage of Black',
            'expected': 'In re Marriage of Black'
        }
    ]
    
    print("🔍 Testing Enhanced Verification Directly")
    print("=" * 80)
    
    for test_case in test_cases:
        citation = test_case['citation']
        extracted_name = test_case['extracted_case_name']
        expected = test_case['expected']
        
        print(f"\n--- Testing: {citation} ---")
        print(f"Extracted case name: {extracted_name}")
        print(f"Expected result: {expected}")
        print("-" * 50)
        
        try:
            result = verifier.verify_citation_enhanced(citation, extracted_name)
            
            print(f"Verification result:")
            print(f"  Verified: {result.get('verified')}")
            print(f"  Canonical name: {result.get('canonical_name')}")
            print(f"  Canonical date: {result.get('canonical_date')}")
            print(f"  Source: {result.get('source')}")
            print(f"  Validation method: {result.get('validation_method')}")
            print(f"  Confidence: {result.get('confidence')}")
            
            if result.get('verified'):
                if result.get('canonical_name') == expected:
                    print(f"✅ CORRECT: Matches expected case name")
                else:
                    print(f"❌ WRONG: Expected '{expected}', got '{result.get('canonical_name')}'")
            else:
                print(f"⚠️  NOT VERIFIED: Enhanced verification failed")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_verification()
