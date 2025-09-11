#!/usr/bin/env python3
"""
Test script to test the EnhancedFallbackVerifier with the Knight case.
This tests the backup verifier that should be used when citation-lookup API v4 fails.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_fallback_verifier import EnhancedFallbackVerifier

def test_backup_verifier_knight():
    """Test the backup verifier with the Knight case."""
    
    print("🔍 Testing EnhancedFallbackVerifier with Knight Case")
    print("=" * 80)
    
    # Initialize the backup verifier
    verifier = EnhancedFallbackVerifier()
    
    # Test the specific Knight citations
    test_cases = [
        {
            'citation': '178 Wn. App. 929',
            'extracted_case_name': 'In re Vulnerable Adult Petition for Knight',
            'description': 'Knight case - Washington Appeals Court'
        },
        {
            'citation': '317 P.3d 1068',
            'extracted_case_name': 'In re Vulnerable Adult Petition for Knight',
            'description': 'Knight case - Pacific Reporter'
        },
        {
            'citation': '188 Wn.2d 114',
            'extracted_case_name': 'In re Marriage of Black',
            'description': 'Black case - Washington Supreme Court (should fail citation-lookup)'
        }
    ]
    
    for test_case in test_cases:
        citation = test_case['citation']
        extracted_name = test_case['extracted_case_name']
        description = test_case['description']
        
        print(f"\n--- Testing: {citation} ---")
        print(f"Description: {description}")
        print(f"Extracted case name: {extracted_name}")
        print("-" * 60)
        
        try:
            # Test the backup verifier directly
            result = verifier.verify_citation_sync(citation, extracted_name)
            
            print(f"Backup verification result:")
            print(f"  Verified: {result.get('verified')}")
            print(f"  Canonical name: {result.get('canonical_name')}")
            print(f"  Canonical date: {result.get('canonical_date')}")
            print(f"  Source: {result.get('source')}")
            print(f"  URL: {result.get('url')}")
            print(f"  Confidence: {result.get('confidence')}")
            
            # Check for data contamination
            if result.get('canonical_name'):
                if 'Gillian Timaeus' in result.get('canonical_name', ''):
                    print(f"🚨 DATA CONTAMINATION DETECTED!")
                    print(f"   Expected: {extracted_name}")
                    print(f"   Got: {result.get('canonical_name')}")
                elif result.get('canonical_name') == extracted_name:
                    print(f"✅ PERFECT MATCH: Backup verifier preserved extracted name")
                elif result.get('canonical_name') and extracted_name:
                    print(f"⚠️  DIFFERENT: Backup verifier found different canonical name")
                    print(f"   This might be correct if the backup found the official case name")
                else:
                    print(f"ℹ️  No canonical name found")
            else:
                print(f"ℹ️  No canonical name returned")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n" + "=" * 80)
    print("🎯 SUMMARY:")
    print("The backup verifier should:")
    print("1. ✅ NOT introduce false positives (like 'Gillian Timaeus')")
    print("2. ✅ Preserve extracted case names when possible")
    print("3. ✅ Provide additional verification when citation-lookup fails")
    print("4. ✅ Use reliable web search sources (Justia, FindLaw, etc.)")

if __name__ == "__main__":
    test_backup_verifier_knight()
