#!/usr/bin/env python3
"""
Comprehensive test script to verify the regex fix works with all test paragraphs from memory
"""

import re

def test_all_paragraphs():
    """Test the corrected regex pattern with all test paragraphs from memory"""
    
    # The corrected pattern from unified_case_name_extractor.py
    pattern = r'([A-Z][A-Za-z0-9&.\'\s-]+(?:\s+[A-Za-z0-9&.\'\s-]+)*?)\s+v\.\s+([A-Z][A-Za-z0-9&.\'\s-]+(?:\s+[A-Za-z0-9&.\'\s-]+)*?)(?=\s*,|\s*\(|$)'
    
    # Test paragraphs from memory
    test_paragraphs = [
        {
            'name': 'Standard Test Paragraph',
            'text': 'A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep\'t of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)',
            'expected_cases': [
                'Convoyant, LLC v. DeepThink, LLC',
                'Carlson v. Glob. Client Sols., LLC', 
                'Dep\'t of Ecology v. Campbell & Gwinn, LLC'
            ]
        },
        {
            'name': 'Pro Se Litigants Test Paragraph',
            'text': 'We have long held that pro se litigants are bound by the same rules of procedure and substantive law as licensed attorneys. Holder v. City of Vancouver, 136 Wn. App. 104, 106, 147 P.3d 641 (2006); In re Marriage of Olson, 69 Wn. App. 621, 626, 850 P.2d 527 (1993) (noting courts are "under no obligation to grant special favors to . . . a pro se litigant."). Thus, a pro se appellant\'s failure to "identify any specific legal issues . . . cite any authority" or comply with procedural rules may still preclude appellate review. State v. Marintorres, 93 Wn. App. 442, 452, 969 P.2d 501 (1999)',
            'expected_cases': [
                'Holder v. City of Vancouver',
                'In re Marriage of Olson',
                'State v. Marintorres'
            ]
        },
        {
            'name': 'Current Test Paragraph (DeSean v. Sanger + State v. Ervin)',
            'text': 'DeSean v. Sanger, 2 Wn. 3d 329, 536 P.3d 191 (2023). State v. Ervin, 169 Wn.2d 815, 239 P.3d 354 (2010)',
            'expected_cases': [
                'DeSean v. Sanger',
                'State v. Ervin'
            ]
        }
    ]
    
    print("Testing corrected regex pattern with all test paragraphs from memory")
    print(f"Pattern: {pattern}")
    print("=" * 80)
    
    for paragraph in test_paragraphs:
        print(f"\n📝 Testing: {paragraph['name']}")
        print(f"Text: {paragraph['text']}")
        print()
        
        # Find all matches in the text
        matches = list(re.finditer(pattern, paragraph['text']))
        
        if matches:
            print(f"✅ Found {len(matches)} case name matches:")
            for i, match in enumerate(matches, 1):
                plaintiff = match.group(1).strip()
                defendant = match.group(2).strip()
                case_name = f"{plaintiff} v. {defendant}"
                print(f"   {i}. '{case_name}'")
                
                # Check if this matches any expected case
                found_expected = False
                for expected in paragraph['expected_cases']:
                    if case_name in expected or expected in case_name:
                        print(f"      ✅ Matches expected: '{expected}'")
                        found_expected = True
                        break
                
                if not found_expected:
                    print(f"      ⚠️  No exact match found in expected cases")
                    print(f"      Expected cases: {paragraph['expected_cases']}")
        else:
            print("❌ No case name matches found")
            print(f"Expected cases: {paragraph['expected_cases']}")
        
        print("-" * 60)

if __name__ == "__main__":
    test_all_paragraphs()
