#!/usr/bin/env python3
"""
Test the fixed WL extraction using comma anchor method
"""

import sys
sys.path.append('src')

from unified_case_extraction_master import UnifiedCaseExtractionMaster

def test_wl_comma_anchor():
    """Test the fixed WL extraction via comma anchor"""
    
    extractor = UnifiedCaseExtractionMaster()
    
    # Test cases
    test_cases = [
        {
            "text": "Doe, Inc. v. Roe, No. MC 21-43 (BAH), 2021 WL 3622166, at *3 (D.D.C. June 3, 2021).",
            "expected": "Doe, Inc. v. Roe",
            "description": "Original failing case with MC docket"
        },
        {
            "text": "Smith v. Jones, No. 2:18-CV-00348-SMJ, 2019 WL 2066127",
            "expected": "Smith v. Jones",
            "description": "Standard WL with docket"
        },
        {
            "text": "Acme Corp. v. XYZ Inc., No. 21-1234, 2021 WL 987654",
            "expected": "Acme Corp. v. XYZ Inc.",
            "description": "WL with simple docket"
        },
    ]
    
    print("=" * 80)
    print("TESTING WL EXTRACTION VIA COMMA ANCHOR")
    print("=" * 80)
    print()
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"Text: {test['text']}")
        
        # Find the WL citation position
        wl_pos = test['text'].find("WL")
        if wl_pos == -1:
            print("ERROR: WL citation not found")
            continue
            
        # Extract using the comma anchor method
        result = extractor._extract_with_comma_anchor(
            text=test['text'],
            citation=test['text'][wl_pos-10:wl_pos+20],
            start_index=wl_pos,
            debug=False
        )
        
        if result:
            print(f"✓ Extracted: '{result.case_name}'")
            print(f"  Method: {result.method}")
            print(f"  Confidence: {result.confidence}")
            
            if result.case_name == test['expected']:
                print("✅ CORRECT!")
            else:
                print(f"❌ Expected: '{test['expected']}'")
        else:
            print("❌ FAILED TO EXTRACT")
        
        print()

if __name__ == "__main__":
    test_wl_comma_anchor()
