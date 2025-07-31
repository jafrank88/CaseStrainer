#!/usr/bin/env python3
"""
Test the enhanced verification fixes to ensure proper citation field search and validation
"""

import requests
import json
from datetime import datetime

def test_enhanced_verification_fixes():
    """Test that our fixes correctly find the cited case, not citing cases"""
    
    print("TESTING ENHANCED VERIFICATION FIXES")
    print("=" * 60)
    
    # Test the problematic citation that was returning wrong results
    test_cases = [
        {
            'citation': '17 L. Ed. 2d 562',
            'expected_case': 'Garrity v. New Jersey',
            'expected_year': '1967',
            'description': 'Previously returned State v. Flynn (2024) - should now return Garrity v. New Jersey (1967)'
        },
        {
            'citation': '385 U.S. 493',
            'expected_case': 'Garrity v. New Jersey', 
            'expected_year': '1967',
            'description': 'Parallel citation for same case'
        },
        {
            'citation': '87 S. Ct. 616',
            'expected_case': 'Garrity v. New Jersey',
            'expected_year': '1967', 
            'description': 'Another parallel citation for same case'
        }
    ]
    
    endpoint = "http://localhost:5001/casestrainer/api/analyze"
    
    for i, test_case in enumerate(test_cases):
        citation = test_case['citation']
        expected_case = test_case['expected_case']
        expected_year = test_case['expected_year']
        description = test_case['description']
        
        print(f"\n[{i+1}/{len(test_cases)}] TESTING: {citation}")
        print(f"Description: {description}")
        print(f"Expected: {expected_case} ({expected_year})")
        print("-" * 50)
        
        # Create test input with context
        test_text = f"In {expected_case} ({expected_year}), the court cited {citation}."
        
        try:
            response = requests.post(
                endpoint,
                json={"text": test_text, "type": "text"},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                citations_found = result.get('citations', [])
                
                if citations_found:
                    citation_result = citations_found[0]
                    verified = citation_result.get('verified', False)
                    canonical_name = citation_result.get('canonical_name', '')
                    canonical_date = citation_result.get('canonical_date', '')
                    source = citation_result.get('source', '')
                    confidence = citation_result.get('confidence', 0.0)
                    
                    print(f"Status: {'✅ VERIFIED' if verified else '❌ UNVERIFIED'}")
                    print(f"Found Case: {canonical_name}")
                    print(f"Found Date: {canonical_date}")
                    print(f"Source: {source}")
                    print(f"Confidence: {confidence}")
                    
                    # Check if the fix worked
                    if verified:
                        if expected_case.lower() in canonical_name.lower():
                            if expected_year in str(canonical_date):
                                print(f"🎯 SUCCESS: Fix worked! Found correct case and year.")
                            else:
                                print(f"⚠️  PARTIAL: Correct case but year mismatch")
                                print(f"   Expected year: {expected_year}")
                                print(f"   Found year: {canonical_date}")
                        else:
                            print(f"❌ FAILED: Still returning wrong case")
                            print(f"   Expected: {expected_case}")
                            print(f"   Found: {canonical_name}")
                            print(f"   This suggests the fix didn't work properly")
                    else:
                        print(f"❌ UNVERIFIED: Citation not verified (could be API issue or missing data)")
                        
                else:
                    print(f"❌ NO CITATIONS: No citations extracted from text")
                    
            else:
                print(f"❌ API ERROR: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
    
    print(f"\n{'='*60}")
    print("SUMMARY OF ENHANCED VERIFICATION FIXES TEST")
    print(f"{'='*60}")
    print("Key fixes implemented:")
    print("1. ✅ Changed Search API query from full-text to citation field search")
    print("2. ✅ Added validation that citation appears in result's citation array")
    print("3. ✅ This should prevent citing cases from being returned as verified")
    print()
    print("If the test shows 'SUCCESS' for the problematic citation, the fixes worked!")
    print("If it still shows wrong cases, we may need additional validation logic.")

if __name__ == "__main__":
    test_enhanced_verification_fixes()
