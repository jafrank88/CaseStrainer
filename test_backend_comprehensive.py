#!/usr/bin/env python3
"""
Comprehensive test script to verify that the backend API filtering is working across different scenarios.
"""

import requests
import json

def test_backend_comprehensive():
    """Test the backend with various citation scenarios."""
    
    base_url = "http://localhost:5001"
    endpoint = "/casestrainer/api/analyze_enhanced"
    
    # Test cases with different scenarios
    test_cases = [
        {
            "name": "Roe v. Wade (should be filtered)",
            "text": "Roe v. Wade, 410 U.S. 113 (1973)."
        },
        {
            "name": "Brown v. Board (should be filtered)",
            "text": "Brown v. Board of Education, 347 U.S. 483 (1954)."
        },
        {
            "name": "Washington case (should be filtered)",
            "text": "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 514 P.3d 643 (2022)."
        },
        {
            "name": "Multiple citations (should be filtered)",
            "text": "A federal court may ask this court to answer a question of Washington law. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 514 P.3d 643 (2022)."
        }
    ]
    
    print("Testing Backend API Filtering - Comprehensive Test")
    print("=" * 80)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Text: {test_case['text']}")
        print("-" * 60)
        
        try:
            response = requests.post(
                f"{base_url}{endpoint}",
                json={"type": "text", "text": test_case['text']},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                citations = result.get('citations', [])
                
                print(f"   Found {len(citations)} citations:")
                
                case_passed = True
                for j, citation in enumerate(citations, 1):
                    canonical_name = citation.get('canonical_name', 'N/A')
                    verified = citation.get('verified', 'N/A')
                    source = citation.get('source', 'N/A')
                    
                    print(f"     {j}. Citation: {citation.get('citation', 'N/A')}")
                    print(f"        Canonical Name: {canonical_name}")
                    print(f"        Verified: {verified}")
                    print(f"        Source: {source}")
                    
                    # Check for web domains
                    if canonical_name and canonical_name != 'N/A':
                        if any(domain in canonical_name.lower() for domain in ['youtube.com', 'google.com', 'cheaperthandirt.com', 'http', 'www.']):
                            print(f"        ⚠️  FAILURE: Web domain detected in canonical name!")
                            case_passed = False
                        else:
                            print(f"        ✓ Canonical name looks valid")
                    else:
                        print(f"        ✓ No canonical name (filtering worked)")
                
                if case_passed:
                    print(f"   ✓ {test_case['name']} - PASSED")
                else:
                    print(f"   ✗ {test_case['name']} - FAILED")
                    all_passed = False
                    
            else:
                print(f"   ✗ API request failed: {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED - Filtering is working correctly!")
    else:
        print("✗ SOME TESTS FAILED - Filtering needs attention")
    
    return all_passed

if __name__ == "__main__":
    success = test_backend_comprehensive()
    if success:
        print("\n🎉 Backend API filtering is working perfectly!")
    else:
        print("\n❌ Backend API filtering has issues") 