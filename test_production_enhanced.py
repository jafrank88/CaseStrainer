#!/usr/bin/env python3
"""
Test the enhanced verification system in production
"""

import requests
import json

def test_production_enhanced_verification():
    """Test enhanced verification in production environment"""
    
    print("TESTING ENHANCED VERIFICATION IN PRODUCTION")
    print("=" * 50)
    
    # Test the problematic citation that was a false positive
    test_data = {
        "text": "This case cites Benckini v. Hawk, 654 F. Supp. 2d 321 (D. Conn. 2009).",
        "use_enhanced_verification": True
    }
    
    try:
        print(f"Testing citation: 654 F. Supp. 2d 321")
        print(f"Sending request to production API...")
        
        response = requests.post(
            "http://localhost:5000/api/analyze_enhanced",
            json=test_data,
            timeout=60
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\nPRODUCTION RESULT:")
            print(f"Status: {result.get('status')}")
            
            citations = result.get('citations', [])
            print(f"Citations found: {len(citations)}")
            
            for i, citation in enumerate(citations):
                print(f"\nCitation {i+1}:")
                print(f"  Citation: {citation.get('citation')}")
                print(f"  Verified: {citation.get('verified')}")
                print(f"  Canonical Name: '{citation.get('canonical_name')}'")
                print(f"  Canonical Date: '{citation.get('canonical_date')}'")
                print(f"  URL: '{citation.get('url')}'")
                print(f"  Source: '{citation.get('source')}'")
                print(f"  Confidence: {citation.get('confidence')}")
                print(f"  Validation Method: {citation.get('validation_method')}")
                
                # Analysis of the specific problematic citation
                if "654 F. Supp. 2d 321" in citation.get('citation', ''):
                    verified = citation.get('verified', False)
                    canonical_name = citation.get('canonical_name')
                    url = citation.get('url')
                    source = citation.get('source')
                    confidence = citation.get('confidence', 0.0)
                    
                    print(f"\n🔍 ANALYSIS OF PROBLEMATIC CITATION:")
                    
                    if verified and canonical_name and canonical_name.strip() and url and url.strip():
                        print(f"  ✅ LEGITIMATE VERIFICATION")
                        print(f"     - Complete canonical data present")
                        print(f"     - Source: {source}")
                        print(f"     - Confidence: {confidence}")
                        print(f"     - Enhanced validation passed")
                        
                        if 'validated' in source.lower():
                            print(f"  🎯 ENHANCED VALIDATION WORKING")
                            print(f"     - Citation passed cross-validation")
                        else:
                            print(f"  ⚠️  BASIC VERIFICATION (no enhanced validation)")
                            
                    elif verified and (not canonical_name or not canonical_name.strip() or not url or not url.strip()):
                        print(f"  ❌ FALSE POSITIVE DETECTED")
                        print(f"     - Verified but missing essential data")
                        print(f"     - ENHANCED VERIFICATION FAILED")
                        
                    else:
                        print(f"  ✅ CORRECTLY UNVERIFIED")
                        print(f"     - Enhanced verification prevented false positive")
                        print(f"     - System working correctly")
        
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"Exception: {str(e)}")

def test_multiple_citations():
    """Test multiple citations including edge cases"""
    
    print(f"\n{'='*60}")
    print("TESTING MULTIPLE CITATIONS WITH ENHANCED VERIFICATION")
    print(f"{'='*60}")
    
    test_cases = [
        {
            "name": "False Positive Test",
            "text": "Benckini v. Hawk, 654 F. Supp. 2d 321 (D. Conn. 2009)",
            "expected": "Should be verified only if legitimate data exists"
        },
        {
            "name": "Valid Citation Test", 
            "text": "Smith v. Jones, 456 F.3d 789 (9th Cir. 2006)",
            "expected": "Should be verified if exists in CourtListener"
        },
        {
            "name": "Non-existent Citation",
            "text": "Fake v. Case, 999 F.3d 999 (1st Cir. 2099)",
            "expected": "Should not be verified"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'-'*40}")
        print(f"TEST: {test_case['name']}")
        print(f"TEXT: {test_case['text']}")
        print(f"EXPECTED: {test_case['expected']}")
        print(f"{'-'*40}")
        
        try:
            response = requests.post(
                "http://localhost:5000/api/analyze_enhanced",
                json={"text": test_case['text'], "use_enhanced_verification": True},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                citations = result.get('citations', [])
                
                if citations:
                    citation = citations[0]
                    verified = citation.get('verified', False)
                    source = citation.get('source', '')
                    confidence = citation.get('confidence', 0.0)
                    
                    print(f"RESULT: Verified={verified}, Source={source}, Confidence={confidence}")
                    
                    if 'validated' in source.lower():
                        print(f"✅ Enhanced validation applied")
                    else:
                        print(f"⚠️  Basic verification used")
                else:
                    print(f"No citations found")
            else:
                print(f"Error: {response.status_code}")
        
        except Exception as e:
            print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_production_enhanced_verification()
    test_multiple_citations()
    
    print(f"\n{'='*60}")
    print("PRODUCTION TESTING COMPLETE")
    print(f"{'='*60}")
    print("Key indicators of success:")
    print("1. Enhanced validation sources (e.g., 'CourtListener-search-validated')")
    print("2. High confidence scores for legitimate citations")
    print("3. Proper rejection of false positives")
    print("4. Cross-validation working between API endpoints")
