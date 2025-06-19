#!/usr/bin/env python3
"""
Test script to verify that non-CourtListener verified citations are saved to the unverified cache.
"""

import os
import sys
import json
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_non_courtlistener_cache():
    """Test that non-CourtListener verified citations are saved to the unverified cache."""
    
    try:
        from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
        
        print("=== Testing Non-CourtListener Citation Cache ===")
        
        # Initialize the verifier
        verifier = EnhancedMultiSourceVerifier()
        
        # Create a mock result that would be returned by LangSearch
        mock_langsearch_result = {
            "verified": True,
            "verified_by": "LangSearch",
            "citation": "123 F.2d 456",
            "case_name": "Test Case v. Test Defendant",
            "confidence": 0.85,
            "explanation": "Verified by LangSearch API",
            "url": "https://example.com/case",
            "details": {"source": "LangSearch"}
        }
        
        # Test the _save_to_unverified_cache function
        print("Testing _save_to_unverified_cache function...")
        verifier._save_to_unverified_cache("123 F.2d 456", mock_langsearch_result)
        
        # Check if the file was created and contains the entry
        cache_path = "data/citations/unverified_citations_with_sources.json"
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Find our test entry
            test_entry = None
            for entry in cache_data:
                if entry.get("citation") == "123 F.2d 456":
                    test_entry = entry
                    break
            
            if test_entry:
                print("✅ Success! Test citation was saved to unverified cache:")
                print(f"   Citation: {test_entry['citation']}")
                print(f"   Source: {test_entry['source']}")
                print(f"   Status: {test_entry['status']}")
                print(f"   Summary: {test_entry['summary']}")
                print(f"   Timestamp: {test_entry['timestamp']}")
            else:
                print("❌ Test citation not found in cache")
                return False
        else:
            print("❌ Cache file was not created")
            return False
        
        # Test that CourtListener results are NOT saved
        print("\nTesting that CourtListener results are NOT saved...")
        mock_courtlistener_result = {
            "verified": True,
            "verified_by": "CourtListener",
            "citation": "456 U.S. 789",
            "case_name": "CourtListener Case",
            "confidence": 0.95,
            "explanation": "Verified by CourtListener API"
        }
        
        # Get the count before adding CourtListener result
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data_before = json.load(f)
        count_before = len(cache_data_before)
        
        # Try to save CourtListener result
        verifier._save_to_unverified_cache("456 U.S. 789", mock_courtlistener_result)
        
        # Check that the count didn't change
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data_after = json.load(f)
        count_after = len(cache_data_after)
        
        if count_before == count_after:
            print("✅ Success! CourtListener results are correctly NOT saved to unverified cache")
        else:
            print(f"❌ Error: CourtListener result was incorrectly saved (count changed from {count_before} to {count_after})")
            return False
        
        # Test updating existing entry
        print("\nTesting update of existing entry...")
        updated_result = {
            "verified": True,
            "verified_by": "LangSearch",
            "citation": "123 F.2d 456",
            "case_name": "Updated Test Case v. Test Defendant",
            "confidence": 0.90,
            "explanation": "Updated verification by LangSearch API",
            "url": "https://example.com/updated-case",
            "details": {"source": "LangSearch", "updated": True}
        }
        
        verifier._save_to_unverified_cache("123 F.2d 456", updated_result)
        
        # Check that the entry was updated
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data_updated = json.load(f)
        
        updated_entry = None
        for entry in cache_data_updated:
            if entry.get("citation") == "123 F.2d 456":
                updated_entry = entry
                break
        
        if updated_entry and updated_entry.get("case_name") == "Updated Test Case v. Test Defendant":
            print("✅ Success! Existing entry was correctly updated")
        else:
            print("❌ Error: Existing entry was not updated correctly")
            return False
        
        print("\n=== All Tests Passed! ===")
        print("The non-CourtListener citation cache functionality is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_non_courtlistener_cache()
    sys.exit(0 if success else 1) 