#!/usr/bin/env python3
"""
Test the case name cleaning method after the regex fix.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_case_name_cleaning():
    """Test that case names are properly cleaned after the regex fix."""
    
    try:
        from src.enhanced_clustering import EnhancedCitationClusterer, ClusteringConfig
        
        config = ClusteringConfig(debug_mode=True)
        clusterer = EnhancedCitationClusterer(config)
        
        print("=== Testing Case Name Cleaning After Regex Fix ===")
        
        # Test cases
        test_cases = [
            "We review statutory interpretation de novo. DeSean v. Sanger",
            "State v. Ervin",
            "In re Marriage of Black",
            "The goal of statutory interpretation is to give effect to the legislature's intentions. Blackmon v. Blackmon"
        ]
        
        for case_name in test_cases:
            cleaned = clusterer._clean_case_name_for_clustering(case_name)
            print(f"Original: '{case_name}'")
            print(f"Cleaned:  '{cleaned}'")
            print()
        
        print("🎯 EXPECTED RESULTS:")
        print("  - 'DeSean v. Sanger' should be extracted (not 'Sean v. Sanger')")
        print("  - Long context phrases should be removed")
        print("  - Only the actual case name should remain")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_case_name_cleaning()
