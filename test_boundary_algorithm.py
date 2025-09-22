#!/usr/bin/env python3
"""
Test the specific boundary detection algorithm for case name extraction.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_extraction_architecture import get_unified_extractor

def test_boundary_algorithm():
    """Test the boundary detection with your specific example."""
    
    # Your example: "In Smith, Inc. v. Jones"
    test_cases = [
        {
            'text': 'In Smith, Inc. v. Jones, the court held...',
            'expected_plaintiff': 'Smith, Inc.',
            'expected_defendant': 'Jones',
            'description': 'Your example: In Smith, Inc. v. Jones'
        },
        {
            'text': 'The Supreme Court held in Spokeo, Inc. v. Robins, 578 U.S. 330',
            'expected_plaintiff': 'Spokeo, Inc.',
            'expected_defendant': 'Robins',
            'description': 'Spokeo case with "held in" prefix'
        },
        {
            'text': 'The court decided Smith v. Jones in favor of plaintiff',
            'expected_plaintiff': 'Smith',
            'expected_defendant': 'Jones', 
            'description': 'Simple case with "The court decided" prefix'
        }
    ]
    
    extractor = get_unified_extractor()
    
    print("🧠 TESTING BOUNDARY DETECTION ALGORITHM")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases):
        print(f"\n🔍 Test {i+1}: {test_case['description']}")
        print(f"📝 Text: {test_case['text']}")
        print(f"🎯 Expected: {test_case['expected_plaintiff']} v. {test_case['expected_defendant']}")
        print("-" * 40)
        
        # Find the v. in the text
        v_pos = test_case['text'].find(' v. ')
        if v_pos == -1:
            print("❌ No 'v.' found in text")
            continue
            
        v_start = v_pos + 1  # Position of 'v'
        v_end = v_pos + 4    # Position after 'v. '
        
        # Test plaintiff extraction (backwards)
        plaintiff = extractor._extract_plaintiff_backwards(test_case['text'], v_start, debug=True)
        print(f"📊 Extracted plaintiff: '{plaintiff}'")
        
        # Test defendant extraction (forwards) 
        defendant = extractor._extract_defendant_forwards(test_case['text'], v_end, debug=True)
        print(f"📊 Extracted defendant: '{defendant}'")
        
        # Check results
        plaintiff_correct = plaintiff == test_case['expected_plaintiff']
        defendant_correct = defendant == test_case['expected_defendant']
        
        print(f"✅ Plaintiff: {'PASS' if plaintiff_correct else 'FAIL'}")
        print(f"✅ Defendant: {'PASS' if defendant_correct else 'FAIL'}")
        
        if plaintiff_correct and defendant_correct:
            print("🎉 OVERALL: PASS")
        else:
            print("❌ OVERALL: FAIL")

if __name__ == "__main__":
    test_boundary_algorithm()
