#!/usr/bin/env python3
"""
Test script for the unified extraction architecture.
This verifies that the new architecture correctly extracts case names and years.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.unified_extraction_architecture import get_unified_extractor

def test_unified_architecture():
    """Test the unified extraction architecture with the standard test cases."""
    
    # Test text with known cases
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    # Expected results
    expected_cases = {
        "200 Wn.2d 72": "Convoyant, LLC v. DeepThink, LLC",
        "171 Wn.2d 486": "Carlson v. Glob. Client Sols., LLC", 
        "146 Wn.2d 1": "Dep't of Ecology v. Campbell & Gwinn, LLC",
        "514 P.3d 643": "Convoyant, LLC v. DeepThink, LLC",
        "256 P.3d 321": "Carlson v. Glob. Client Sols., LLC",
        "43 P.3d 4": "Dep't of Ecology v. Campbell & Gwinn, LLC"
    }
    
    print("🧪 Testing Unified Extraction Architecture")
    print("=" * 50)
    
    # Get the unified extractor
    extractor = get_unified_extractor()
    
    # Test each citation
    all_passed = True
    for citation, expected_name in expected_cases.items():
        print(f"\n📋 Testing citation: {citation}")
        
        # Find position in text
        start_pos = test_text.find(citation)
        end_pos = start_pos + len(citation) if start_pos != -1 else None
        
        if start_pos == -1:
            print(f"❌ Citation not found in text")
            all_passed = False
            continue
        
        # Extract using unified architecture
        result = extractor.extract_case_name_and_year(
            text=test_text,
            citation=citation,
            start_index=start_pos,
            end_index=end_pos,
            debug=True
        )
        
        print(f"   Extracted: '{result.case_name}'")
        print(f"   Expected:  '{expected_name}'")
        print(f"   Year:      '{result.year}'")
        print(f"   Method:    '{result.method}'")
        print(f"   Confidence: {result.confidence}")
        
        # Check if extraction is correct
        if result.case_name == expected_name:
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL - Expected '{expected_name}', got '{result.case_name}'")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests PASSED! Unified architecture is working correctly.")
    else:
        print("❌ Some tests FAILED. Architecture needs improvement.")
    
    return all_passed

def test_api_integration():
    """Test the API integration with the new architecture."""
    import requests
    import json
    
    print("\n🌐 Testing API Integration")
    print("=" * 30)
    
    # Test data
    data = {
        'text': 'A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep\'t of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)'
    }
    
    try:
        # Test local API
        response = requests.post('http://localhost:5000/casestrainer/api/analyze', json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Response: {response.status_code}")
            print(f"   Citations found: {result['result']['citations_found']}")
            print(f"   Clusters created: {result['result']['clusters_created']}")
            print(f"   Contamination rate: {result['result']['data_separation_validation']['contamination_rate']}")
            
            print("\n📋 Citations:")
            for i, citation in enumerate(result['result']['citations']):
                print(f"   {i+1}. {citation['citation']} -> {citation['extracted_case_name']}")
            
            return True
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API Test Failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Unified Extraction Architecture Tests")
    
    # Test 1: Direct architecture testing
    architecture_passed = test_unified_architecture()
    
    # Test 2: API integration testing
    api_passed = test_api_integration()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(f"   Architecture Tests: {'✅ PASS' if architecture_passed else '❌ FAIL'}")
    print(f"   API Integration:    {'✅ PASS' if api_passed else '❌ FAIL'}")
    
    if architecture_passed and api_passed:
        print("\n🎉 ALL TESTS PASSED! The unified architecture is working correctly.")
    else:
        print("\n❌ SOME TESTS FAILED. The architecture needs further work.")

