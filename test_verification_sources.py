#!/usr/bin/env python3
"""
Test script to check what each verification source returns, including URLs.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2 as UnifiedCitationProcessor

def test_verification_sources():
    """Test each verification source to see what they return."""
    
    processor = UnifiedCitationProcessor()
    
    # Test citation that should be found in CourtListener - use a well-known US Supreme Court case
    test_citation = "410 U.S. 113"
    
    print("=== TESTING VERIFICATION SOURCES ===")
    print(f"Test citation: {test_citation}")
    print()
    
    # Test each verification method individually
    verification_methods = [
        ("CourtListener", processor._verify_with_courtlistener),
        ("LangSearch", processor._verify_with_langsearch),
        ("Database", processor._verify_with_database),
        ("Landmark Cases", processor._verify_with_landmark_cases),
        ("Fuzzy Matching", processor._verify_with_fuzzy_matching),
    ]
    
    for method_name, method_func in verification_methods:
        print(f"Testing {method_name}:")
        try:
            result = method_func(test_citation)
            print(f"  Verified: {result.get('verified', False)}")
            print(f"  Case name: '{result.get('case_name', 'None')}'")
            print(f"  URL: '{result.get('url', 'None')}'")
            print(f"  Court: '{result.get('court', 'None')}'")
            print(f"  Date: '{result.get('date', 'None')}'")
            print(f"  Error: '{result.get('error', 'None')}'")
            print()
        except Exception as e:
            print(f"  Error: {e}")
            print()
    
    print("=== SUMMARY ===")
    print("Sources that should provide URLs:")
    print("- CourtListener: Should provide URLs to case pages")
    print("- LangSearch: May provide URLs to legal documents")
    print("- Database: May provide URLs if stored")
    print("- Landmark Cases: May provide URLs to landmark case pages")
    print("- Fuzzy Matching: Typically doesn't provide URLs")

if __name__ == "__main__":
    test_verification_sources() 