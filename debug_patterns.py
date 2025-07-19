#!/usr/bin/env python3
"""
Debug script to check citation patterns in text
"""

def debug_citation_patterns():
    """Debug citation pattern matching"""
    print("🔍 Debugging Citation Patterns")
    print("=" * 40)
    
    # Test text
    test_text = """A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)"""
    
    print(f"Original text: {test_text}")
    print(f"Text length: {len(test_text)} characters")
    print(f"Word count: {len(test_text.split())} words")
    
    # Check for numbers
    has_numbers = any(char.isdigit() for char in test_text)
    print(f"Has numbers: {has_numbers}")
    
    # Check patterns
    text_upper = test_text.upper()
    print(f"Text in uppercase: {text_upper}")
    
    patterns = [
        'U.S.', 'F.', 'F.2D', 'F.3D', 'F.2d', 'F.3d', 'S.CT.', 'L.ED.', 
        'P.2D', 'P.3D', 'P.2d', 'P.3d', 'A.2D', 'A.3D', 'A.2d', 'A.3d',
        'WN.2D', 'WN.APP.', 'WN.2d', 'WN.APP', 'WASH.2D', 'WASH.APP.',
        'WASH.2d', 'WASH.APP'
    ]
    
    print("\nChecking patterns:")
    found_patterns = []
    for pattern in patterns:
        if pattern in text_upper:
            found_patterns.append(pattern)
            print(f"  ✅ Found: {pattern}")
        else:
            print(f"  ❌ Not found: {pattern}")
    
    print(f"\nFound {len(found_patterns)} patterns: {found_patterns}")
    
    # Check for specific citations in the text
    print("\nLooking for specific citations:")
    citations = ['200 Wn.2d 72', '514 P.3d 643', '171 Wn.2d 486', '256 P.3d 321', '146 Wn.2d 1', '43 P.3d 4']
    for citation in citations:
        if citation in test_text:
            print(f"  ✅ Found citation: {citation}")
        else:
            print(f"  ❌ Not found: {citation}")

if __name__ == "__main__":
    debug_citation_patterns() 