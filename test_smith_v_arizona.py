#!/usr/bin/env python3
"""
Test script for Smith v. Arizona citation extraction
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from extract_case_name import extract_case_name_from_context

def test_smith_v_arizona():
    """Test extraction of Smith v. Arizona from the context in the Washington Supreme Court opinion"""
    
    print("Testing Smith v. Arizona citation extraction...")
    print("=" * 50)
    
    # Test the specific context from the Washington Supreme Court opinion
    test_cases = [
        {
            'citation': '602 U.S. 779',
            'context': 'Smith v. Arizona,',
            'expected': 'Smith v. Arizona',
            'description': 'First citation in sequence'
        },
        {
            'citation': '144 S. Ct. 1785',
            'context': 'Smith v. Arizona, 602 U.S. 779,',
            'expected': 'Smith v. Arizona',
            'description': 'Second citation in sequence'
        },
        {
            'citation': '219 L.Ed. 2d 420',
            'context': 'Smith v. Arizona, 602 U.S. 779, 144 S. Ct. 1785,',
            'expected': 'Smith v. Arizona',
            'description': 'Third citation in sequence (L.Ed.)'
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
    test_smith_v_arizona() 