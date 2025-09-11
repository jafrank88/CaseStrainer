"""
Test script for verifying case name extraction with name prefixes.
"""

import sys
import os
import json
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.unified_case_name_extractor_v2 import get_unified_extractor

def run_tests():
    """Run test cases for case name extraction."""
    extractor = get_unified_extractor()
    
    test_cases = [
        {
            "description": "Basic name with prefix",
            "text": "In the case of Smith v. DeSean, the court held that...",
            "expected": "Smith v. DeSean"
        },
        {
            "description": "Name with prefix and space",
            "text": "The decision in Johnson v. De Sean established that...",
            "expected": "Johnson v. DeSean"
        },
        {
            "description": "Multiple name parts with prefix",
            "text": "As held in Smith & Wesson v. DeSean O'Malley, the rule is...",
            "expected": "Smith & Wesson v. DeSean O'Malley"
        },
        {
            "description": "Name with Mc prefix",
            "text": "The court in McDonald v. Smith ruled that...",
            "expected": "McDonald v. Smith"
        },
        {
            "description": "Name with O' prefix",
            "text": "In O'Malley v. Johnson, the court found...",
            "expected": "O'Malley v. Johnson"
        },
        {
            "description": "Name with Van prefix",
            "text": "The case of Van Halen v. Smith established...",
            "expected": "Van Halen v. Smith"
        }
    ]

    print("Running name extraction tests...\n" + "="*50)
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['description']}")
        print("-" * (len(test['description']) + 8))
        print(f"Input:    {test['text']}")
        
        try:
            result = extractor.extract_case_name_and_date(test['text'], debug=True)
            extracted = result.case_name
            print(f"Extracted: {extracted}")
            print(f"Expected:  {test['expected']}")
            
            if extracted.lower() == test['expected'].lower():
                print("✅ PASSED")
                passed += 1
            else:
                print("❌ FAILED")
                failed += 1
                print(f"  - Debug: {result.debug_info}")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"Tests completed: {passed + failed} total, {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
