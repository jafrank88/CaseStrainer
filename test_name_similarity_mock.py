#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify name similarity matching with mock CourtListener results.
This simulates the scenario where multiple results are returned for the same citation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from name_similarity_matcher import select_best_courtlistener_result

def test_mock_courtlistener_results():
    """Test name similarity matching with mock CourtListener results."""
    
    print("Testing Name Similarity Matching with Mock CourtListener Results")
    print("=" * 70)
    
    # Mock CourtListener API results for citation "136 S. Ct. 1083"
    # This simulates the scenario where multiple cases share the same citation
    mock_results = [
        {
            "clusters": [
                {
                    "case_name": "Friedrichs v. Cal. Teachers Ass'n",
                    "date_filed": "2016-01-11",
                    "absolute_url": "/opinion/8176151/friedrichs-v-cal-teachers-assn/"
                }
            ]
        },
        {
            "clusters": [
                {
                    "case_name": "Luis v. United States",
                    "date_filed": "2016-03-29", 
                    "absolute_url": "/opinion/8176152/luis-v-united-states/"
                }
            ]
        },
        {
            "clusters": [
                {
                    "case_name": "United States v. Luis",
                    "date_filed": "2016-03-29",
                    "absolute_url": "/opinion/8176153/united-states-v-luis/"
                }
            ]
        }
    ]
    
    # Test cases with different extracted case names
    test_cases = [
        {
            "extracted_name": "Luis v. United States",
            "expected_best": "Luis v. United States"
        },
        {
            "extracted_name": "United States v. Luis", 
            "expected_best": "United States v. Luis"
        },
        {
            "extracted_name": "Friedrichs v. Cal. Teachers Ass'n",
            "expected_best": "Friedrichs v. Cal. Teachers Ass'n"
        },
        {
            "extracted_name": "Luis v. U.S.",
            "expected_best": "Luis v. United States"  # Should match closest
        },
        {
            "extracted_name": None,  # No extracted name
            "expected_best": "Friedrichs v. Cal. Teachers Ass'n"  # Should return first
        }
    ]
    
    print(f"Mock results contain {len(mock_results)} cases:")
    for i, result in enumerate(mock_results):
        case_name = result['clusters'][0]['case_name']
        print(f"  {i+1}. {case_name}")
    print()
    
    # Test each case
    for i, test_case in enumerate(test_cases):
        extracted_name = test_case["extracted_name"]
        expected_best = test_case["expected_best"]
        
        print(f"Test {i+1}: Extracted name = '{extracted_name}'")
        print("-" * 50)
        
        # Select best result using name similarity matching
        best_result = select_best_courtlistener_result(
            mock_results, 
            extracted_name, 
            debug=True
        )
        
        if best_result:
            actual_best = best_result['clusters'][0]['case_name']
            
            if actual_best == expected_best:
                print(f"✅ SUCCESS: Selected '{actual_best}' (expected: '{expected_best}')")
            else:
                print(f"❌ FAILURE: Selected '{actual_best}' (expected: '{expected_best}')")
        else:
            print(f"❌ FAILURE: No result selected")
        
        print()
    
    print("=" * 70)
    print("Summary: Name similarity matching test completed!")
    
    # Test the specific Luis v. United States scenario
    print("\nSpecific Luis v. United States Test:")
    print("-" * 40)
    
    extracted_name = "Luis v. United States"
    best_result = select_best_courtlistener_result(mock_results, extracted_name, debug=False)
    
    if best_result:
        selected_name = best_result['clusters'][0]['case_name']
        if selected_name == "Luis v. United States":
            print(f"✅ LUIS TEST PASSED: Correctly selected '{selected_name}'")
            print("   This resolves the original issue where 'Friedrichs v. Cal. Teachers Ass'n' was incorrectly selected")
        else:
            print(f"❌ LUIS TEST FAILED: Selected '{selected_name}' instead of 'Luis v. United States'")
    else:
        print("❌ LUIS TEST FAILED: No result selected")

if __name__ == '__main__':
    test_mock_courtlistener_results()
