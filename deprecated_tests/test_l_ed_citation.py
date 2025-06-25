#!/usr/bin/env python3
"""
Test script to debug L.Ed. citations
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from extract_case_name import extract_case_name_from_context

def test_l_ed_citation():
    """Test L.Ed. citation extraction"""
    
    print("Testing L.Ed. citation extraction...")
    print("=" * 50)
    
    # Test the specific L.Ed. citation
    test_cases = [
        {
            'citation': '219 L.Ed. 2d 420',
            'context': 'Some context here',
            'description': 'L.Ed. citation with generic context'
        },
        {
            'citation': '219 L.Ed. 2d 420',
            'context': 'Id.',
            'description': 'L.Ed. citation with Id. context'
        },
        {
            'citation': '219 L.Ed. 2d 420',
            'context': 'Case name v. Another Party',
            'description': 'L.Ed. citation with case name context'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['citation']}")
        print(f"Context: {test_case['context']}")
        print(f"Description: {test_case['description']}")
        
        try:
            result = extract_case_name_from_context(test_case['context'], test_case['citation'])
            print(f"Result: {result}")
            
            if result:
                print("✅ Found case name")
            else:
                print("❌ No case name extracted")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_l_ed_citation() 