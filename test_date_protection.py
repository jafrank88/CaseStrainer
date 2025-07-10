#!/usr/bin/env python3
"""
Test the date protection mechanisms to ensure extracted dates are not overwritten.
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import CitationResult
from src.standalone_citation_parser import DateExtractor, safe_set_extracted_date, validate_citation_dates

def test_date_protection():
    """Test that date protection mechanisms work correctly."""
    
    print("=== TESTING DATE PROTECTION MECHANISMS ===")
    print()
    
    # Test 1: Safe assignment with good values
    print("Test 1: Safe assignment with good values")
    citation = CitationResult(citation="171 Wash. 2d 486")
    
    # First assignment should work
    result1 = safe_set_extracted_date(citation, "2011-01-01", "test1")
    print(f"  First assignment: {result1}, extracted_date: '{citation.extracted_date}'")
    
    # Second assignment with better value should work
    result2 = safe_set_extracted_date(citation, "2011-05-12", "test2")
    print(f"  Second assignment (better): {result2}, extracted_date: '{citation.extracted_date}'")
    
    # Third assignment with worse value should be skipped
    result3 = safe_set_extracted_date(citation, "2011", "test3")
    print(f"  Third assignment (worse): {result3}, extracted_date: '{citation.extracted_date}'")
    
    # Empty assignment should be skipped
    result4 = safe_set_extracted_date(citation, "", "test4")
    print(f"  Empty assignment: {result4}, extracted_date: '{citation.extracted_date}'")
    
    print()
    
    # Test 2: Validation
    print("Test 2: Date validation")
    good_citation = CitationResult(citation="test1")
    good_citation.extracted_date = "2011-01-01"
    print(f"  Good citation validation: {validate_citation_dates(good_citation)}")
    
    bad_citation1 = CitationResult(citation="test2")
    bad_citation1.extracted_date = ""
    print(f"  Bad citation (empty string) validation: {validate_citation_dates(bad_citation1)}")
    
    bad_citation2 = CitationResult(citation="test3")
    bad_citation2.extracted_date = "N/A"
    print(f"  Bad citation ('N/A') validation: {validate_citation_dates(bad_citation2)}")
    
    print()
    
    # Test 3: Direct extraction test
    print("Test 3: Direct extraction test")
    test_text = "In State v. Smith, 171 Wash. 2d 486 (2011), the court held..."
    
    # Find citation position
    citation_text = "171 Wash. 2d 486"
    start_pos = test_text.find(citation_text)
    end_pos = start_pos + len(citation_text)
    
    print(f"  Citation position: {start_pos}-{end_pos}")
    
    # Extract date using DateExtractor
    extracted_date = DateExtractor.extract_date_from_context(test_text, start_pos, end_pos)
    print(f"  Extracted date: '{extracted_date}'")
    
    # Create citation and set date safely
    test_citation = CitationResult(citation=citation_text)
    safe_set_extracted_date(test_citation, extracted_date, "direct_test")
    print(f"  Final extracted_date: '{test_citation.extracted_date}'")
    
    # Validate
    print(f"  Validation: {validate_citation_dates(test_citation)}")
    
    print()
    
    # Test 4: Multiple extraction attempts
    print("Test 4: Multiple extraction attempts (should preserve best result)")
    multi_citation = CitationResult(citation="test4")
    
    # Simulate multiple extraction attempts
    attempts = [
        ("", "failed_extraction"),
        ("2011", "basic_extraction"),
        ("2011-01-01", "enhanced_extraction"),
        ("", "another_failed_attempt"),
        ("2011-05-12", "best_extraction")
    ]
    
    for date_value, source in attempts:
        safe_set_extracted_date(multi_citation, date_value, source)
        print(f"  Attempt '{source}' with '{date_value}': extracted_date = '{multi_citation.extracted_date}'")
    
    print(f"  Final result: '{multi_citation.extracted_date}'")
    print(f"  Validation: {validate_citation_dates(multi_citation)}")
    
    print()
    print("✅ Date protection tests completed!")

if __name__ == "__main__":
    test_date_protection() 