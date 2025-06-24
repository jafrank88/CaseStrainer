#!/usr/bin/env python3
"""
Test script for improved case name extraction with anchored regex patterns
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from extract_case_name import extract_case_name_from_context

def test_extraction():
    """Test the improved extraction logic with problematic citations"""
    
    # Test cases with context BEFORE the citation (not including the citation)
    test_cases = [
        {
            'citation': '2006 WL 3801910',
            'context': 'The court in Wyoming v. U.S. Department of Energy,',
            'expected': 'Wyoming v. U.S. Department of Energy'
        },
        {
            'citation': '2011 WL 2160468',
            'context': 'In the case of Benson v. State of Wyoming,',
            'expected': 'Benson v. State of Wyoming'
        },
        {
            'citation': '2010 WL 4683851',
            'context': 'The decision in Some other case v. Another Party,',
            'expected': 'Some other case v. Another Party'
        },
        {
            'citation': '123 F.3d 456',
            'context': 'As held in Smith v. Jones,',
            'expected': 'Smith v. Jones'
        },
        {
            'citation': '456 U.S. 789',
            'context': 'The Supreme Court in Brown v. Board of Education,',
            'expected': 'Brown v. Board of Education'
        }
    ]
    
    print("Testing improved case name extraction...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['citation']}")
        print(f"Context: {test_case['context']}")
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
    test_extraction() 