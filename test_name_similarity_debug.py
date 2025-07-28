#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug test for name similarity matching to understand why it's not working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_name_similarity_debug():
    """Debug the name similarity matching with detailed output."""
    
    print("Debugging Name Similarity Matching")
    print("=" * 50)
    
    try:
        from name_similarity_matcher import select_best_courtlistener_result, calculate_case_name_similarity
        
        # Test the exact scenario from the focused test
        extracted_case_name = "Luis v. United States"
        
        # Mock CourtListener results (matching the structure from the focused test)
        mock_results = [
            {
                "canonical_name": "Friedrichs v. Cal. Teachers Ass'n",
                "canonical_date": "2016",
                "url": "https://www.courtlistener.com/opinion/8176151/friedrichs-v-cal-teachers-assn/"
            },
            {
                "canonical_name": "Luis v. United States", 
                "canonical_date": "2016",
                "url": "https://www.courtlistener.com/opinion/8176152/luis-v-united-states/"
            }
        ]
        
        print(f"Extracted case name: '{extracted_case_name}'")
        print(f"Number of mock results: {len(mock_results)}")
        print()
        
        # Test individual similarities
        print("Individual similarity calculations:")
        for i, result in enumerate(mock_results):
            case_name = result.get('canonical_name')
            similarity = calculate_case_name_similarity(extracted_case_name, case_name)
            print(f"  Result {i+1}: '{case_name}'")
            print(f"    Similarity: {similarity:.3f}")
            print()
        
        # Test the selection function with debug
        print("Running select_best_courtlistener_result with debug:")
        best_result = select_best_courtlistener_result(mock_results, extracted_case_name, debug=True)
        
        print(f"\nFinal selected result: {best_result.get('canonical_name') if best_result else 'None'}")
        
        # Check if the correct result was selected
        if best_result and "Luis" in best_result.get('canonical_name', ''):
            print("✅ Name similarity matching worked correctly!")
            return True
        else:
            print("❌ Name similarity matching selected the wrong result")
            
            # Additional debugging
            print("\nDebugging the issue:")
            print("The function is looking for case names in these fields:")
            for i, result in enumerate(mock_results):
                print(f"  Result {i+1}:")
                print(f"    clusters: {result.get('clusters', 'NOT FOUND')}")
                print(f"    case_name: {result.get('case_name', 'NOT FOUND')}")
                print(f"    caseName: {result.get('caseName', 'NOT FOUND')}")
                print(f"    name: {result.get('name', 'NOT FOUND')}")
                print(f"    canonical_name: {result.get('canonical_name', 'NOT FOUND')}")
            
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_name_similarity_debug()
