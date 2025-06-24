#!/usr/bin/env python3
"""
Test script for Bluebook citation format handling
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from extract_case_name import extract_case_name_from_context

def test_bluebook_citations():
    """Test extraction with proper Bluebook citation format"""
    
    print("Testing Bluebook citation format handling...")
    print("=" * 50)
    
    # Test the specific Bluebook format citations
    test_cases = [
        {
            'citation': '219 L.Ed.2d 420',
            'context': 'Smith v. Arizona, 602 U.S. 779, 144 S.Ct. 1785,',
            'expected': 'Smith v. Arizona',
            'description': 'L.Ed.2d citation with proper Bluebook format'
        },
        {
            'citation': '144 S.Ct. 1785',
            'context': 'Smith v. Arizona, 602 U.S. 779,',
            'expected': 'Smith v. Arizona',
            'description': 'S.Ct. citation with proper Bluebook format'
        },
        {
            'citation': '602 U.S. 779',
            'context': 'Smith v. Arizona,',
            'expected': 'Smith v. Arizona',
            'description': 'U.S. citation with proper Bluebook format'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['citation']}")
        print(f"Context: {test_case['context']}")
        print(f"Description: {test_case['description']}")
        print(f"Expected: {test_case['expected']}")
        
        try:
            result = extract_case_name_from_context(test_case['context'], test_case['citation'])
            print(f"Result: {result}")
            
            if result == test_case['expected']:
                print("✅ PASS")
            else:
                print("❌ FAIL")
                print(f"Expected: '{test_case['expected']}'")
                print(f"Got: '{result}'")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_bluebook_citations() 