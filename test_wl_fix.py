#!/usr/bin/env python3
"""
Test the fixed WL extraction
"""

import sys
sys.path.append('src')

from unified_case_extraction_master import UnifiedCaseExtractionMaster

def test_wl_fix():
    """Test the fixed WL extraction"""
    
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
    print("TESTING FIXED WL EXTRACTION")
    print("=" * 80)
    print()
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['description']}")
        print(f"Text: {test['text']}")
        
        # Find the citation position
        citation_pos = test['text'].find("WL")
        if citation_pos == -1:
            print("ERROR: WL citation not found")
            continue
            
        # Extract using the special format handler
        result = extractor._extract_special_citation_formats(
            text=test['text'],
            citation=test['text'][citation_pos-10:citation_pos+20],
            start_index=citation_pos,
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
    test_wl_fix()
