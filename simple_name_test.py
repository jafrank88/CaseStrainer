"""
Simple test script for name extraction functionality.
"""

import sys
from src.unified_case_name_extractor_v2 import get_unified_extractor

def test_name_extraction():
    extractor = get_unified_extractor()
    
    test_cases = [
        ("In the case of Smith v. DeSean, the court held that...", "Smith v. DeSean"),
        ("The decision in Johnson v. De Sean established that...", "Johnson v. DeSean"),
        ("As held in Smith & Wesson v. DeSean O'Malley, the rule is...", "Smith & Wesson v. DeSean O'Malley"),
        ("The court in McDonald v. Smith ruled that...", "McDonald v. Smith"),
        ("In O'Malley v. Johnson, the court found...", "O'Malley v. Johnson"),
        ("The case of Van Halen v. Smith established...", "Van Halen v. Smith")
    ]
    
    print("Testing name extraction...\n" + "="*50)
    
    for i, (text, expected) in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print(f"Input:    {text}")
        
        try:
            result = extractor.extract_case_name_and_date(text, debug=True)
            extracted = result.case_name
            print(f"Extracted: {extracted}")
            print(f"Expected:  {expected}")
            
            if extracted.lower() == expected.lower():
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_name_extraction()
