#!/usr/bin/env python3
"""
Test script for "Id." citation handling
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from extract_case_name import extract_case_name_from_context

def test_id_citations():
    """Test that "Id." citations return the most recently extracted case name"""
    
    print("Testing 'Id.' citation handling...")
    print("=" * 50)
    
    # Test sequence: first extract a case name, then test "Id." citation
    test_sequence = [
        {
            'citation': '182 Wn.2d 398',
            'context': 'Utter v. Building Industry Ass\'n',
            'expected': 'Utter v. Building Industry Ass\'n',
            'description': 'First citation - should extract case name'
        },
        {
            'citation': '341 P.3d 953',
            'context': 'Id.',
            'expected': 'Utter v. Building Industry Ass\'n',
            'description': 'Id. citation - should return previous case name'
        },
        {
            'citation': '166 Wn.2d 974',
            'context': 'Putman v. Wenatchee Valley Medical Center',
            'expected': 'Putman v. Wenatchee Valley Medical Center',
            'description': 'New citation - should extract new case name'
        },
        {
            'citation': '216 P.3d 374',
            'context': 'Id.',
            'expected': 'Putman v. Wenatchee Valley Medical Center',
            'description': 'Another Id. citation - should return previous case name'
        }
    ]
    
    for i, test_case in enumerate(test_sequence, 1):
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
    test_id_citations() 