#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Focused test to verify specific citation processing issues after 500 error fix.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_luis_v_united_states():
    """Test the specific Luis v. United States canonical name issue."""
    
    print("Testing Luis v. United States Issue")
    print("=" * 40)
    
    try:
        # Test the name similarity matching directly
        from name_similarity_matcher import select_best_courtlistener_result
        
        # Simulate the Luis v. United States scenario
        extracted_case_name = "Luis v. United States"
        
        # Mock CourtListener results (similar to what we get from the API)
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
        
        # Test name similarity matching
        best_result = select_best_courtlistener_result(mock_results, extracted_case_name)
        
        print(f"Extracted case name: {extracted_case_name}")
        print(f"Best match result: {best_result.get('canonical_name') if best_result else 'None'}")
        
        if best_result and "Luis" in best_result.get('canonical_name', ''):
            print("✅ Name similarity matching is working correctly!")
            return True
        else:
            print("❌ Name similarity matching is not selecting the correct result")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_cluster_propagation():
    """Test fallback cluster canonical data propagation."""
    
    print("\nTesting Fallback Cluster Propagation")
    print("=" * 40)
    
    try:
        from citation_clustering import propagate_canonical_date_within_clusters
        from models import CitationResult
        
        # Create mock fallback cluster citations
        citations = [
            CitationResult(
                citation="196 Wn. 2d 285",
                extracted_case_name="Davison v. State",
                extracted_date="2020",
                canonical_name=None,
                canonical_date=None,
                verified=False
            ),
            CitationResult(
                citation="466 P.3d 231", 
                extracted_case_name="Davison v. State",
                extracted_date="2020",
                canonical_name="Davison v. State",  # This one has canonical data
                canonical_date="2020",
                verified=True
            )
        ]
        
        # Test propagation
        print("Before propagation:")
        for i, citation in enumerate(citations):
            print(f"  Citation {i+1}: {citation.citation}")
            print(f"    canonical_name: {citation.canonical_name}")
            print(f"    canonical_date: {citation.canonical_date}")
        
        # Apply propagation logic
        propagate_canonical_date_within_clusters(citations)
        
        print("\nAfter propagation:")
        for i, citation in enumerate(citations):
            print(f"  Citation {i+1}: {citation.citation}")
            print(f"    canonical_name: {citation.canonical_name}")
            print(f"    canonical_date: {citation.canonical_date}")
        
        # Check if propagation worked
        all_have_canonical = all(c.canonical_name is not None for c in citations)
        
        if all_have_canonical:
            print("✅ Canonical data propagation is working!")
            return True
        else:
            print("❌ Canonical data propagation is not working correctly")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all focused tests."""
    
    print("Focused Citation Processing Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: Luis v. United States name similarity
    results.append(test_luis_v_united_states())
    
    # Test 2: Fallback cluster propagation
    results.append(test_fallback_cluster_propagation())
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    if all(results):
        print("✅ All tests passed! Citation processing should be working correctly.")
    else:
        print("❌ Some tests failed. Issues remain to be fixed.")
        
    return all(results)

if __name__ == '__main__':
    main()
