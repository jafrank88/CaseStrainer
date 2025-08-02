#!/usr/bin/env python3
"""
Test script to verify legal citation extraction for case names with years in parentheses.
"""
import sys
import os
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the enhanced extractor
from scripts.enhanced_extraction_improvements import EnhancedCaseNameExtractor

def test_case_name_extraction():
    """Test case name extraction with various patterns including years in parentheses."""
    test_cases = [
        # Basic case with year in parentheses
        ("In the case of State v. Gentry (1995), the court held that...", 
         ["State v. Gentry"]),
        
        # Multiple citations with years
        ("As established in Smith v. Jones (1990) and later in State v. Gentry (1995), the standard is...",
         ["Smith v. Jones", "State v. Gentry"]),
        
        # With citation numbers
        ("See State v. Gentry (1995) 11 Cal.4th 1, 900 P.2d 1, 44 Cal.Rptr.2d 441",
         ["State v. Gentry"]),
        
        # With punctuation
        ("The court in State v. Gentry (1995), 11 Cal.4th 1, established that...",
         ["State v. Gentry"]),
        
        # Multiple cases in one sentence
        ("Compare State v. Gentry (1995) 11 Cal.4th 1 with People v. Smith (2000) 24 Cal.4th 1",
         ["State v. Gentry", "People v. Smith"])
    ]
    
    extractor = EnhancedCaseNameExtractor()
    all_passed = True
    
    for i, (text, expected) in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Input: {text}")
        
        results = extractor.extract_case_names(text)
        extracted = [r.name for r in results]
        
        print(f"  Extracted: {extracted}")
        print(f"  Expected: {expected}")
        
        # Check if all expected cases were found
        passed = all(case in extracted for case in expected)
        if passed:
            print("  ✓ PASSED")
        else:
            print(f"  ✗ FAILED - Missing: {set(expected) - set(extracted)}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("Testing case name extraction with years in parentheses...")
    success = test_case_name_extraction()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
