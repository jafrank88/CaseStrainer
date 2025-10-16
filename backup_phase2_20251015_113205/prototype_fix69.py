#!/usr/bin/env python3
"""
Quick prototype for Fix #69: Comma-Anchored Case Name Extraction
Test with actual problem cases from 25-2808.pdf
"""

import re

def normalize_whitespace(text):
    """Apply Fix #68 normalization"""
    normalized = text.replace('\n', ' ')
    normalized = normalized.replace('\t', ' ')
    normalized = normalized.replace('\ufffd', "'")
    normalized = normalized.replace('�', "'")
    normalized = normalized.replace('\u2018', "'")
    normalized = normalized.replace('\u2019', "'")
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()

def extract_with_comma_anchor(text, citation, start_index):
    """
    Prototype of comma-anchored extraction
    
    Strategy:
    1. Find comma immediately before citation
    2. Work backwards to find case name
    3. Return full case name
    """
    print(f"\n{'='*80}")
    print(f"TESTING: {citation}")
    print(f"Position: {start_index}")
    print(f"{'='*80}")
    
    # Step 1: Find comma before citation (within 5 chars)
    pre_citation = text[max(0, start_index - 10):start_index]
    print(f"Pre-citation text: '{pre_citation}'")
    
    if ',' not in pre_citation:
        print("[X] No comma found - would fall back to other methods")
        return None
    
    # Find comma position
    comma_offset = pre_citation.rfind(',')
    comma_pos = start_index - (len(pre_citation) - comma_offset)
    print(f"[OK] Comma found at position {comma_pos}")
    
    # Step 2: Get context before comma (400 chars)
    search_start = max(0, comma_pos - 400)
    potential_case_name = text[search_start:comma_pos]
    print(f"Context length: {len(potential_case_name)} chars")
    print(f"Raw context: '{potential_case_name[-150:]}'")
    
    # Step 3: Normalize whitespace
    potential_case_name = normalize_whitespace(potential_case_name)
    print(f"Normalized: '{potential_case_name[-150:]}'")
    
    # Step 4: Extract case name using right-anchored pattern
    # Match case name that ENDS at the comma position
    # Look for: [Capital]...text... v. ...text...$ ($ = end of string)
    
    patterns = [
        # Pattern 1: Full case name with "v." (greedy)
        r'([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})$',
        
        # Pattern 2: After sentence boundary
        r'(?:^|[.!?]\s+)([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})$',
        
        # Pattern 3: After quotation
        r'["\']?\s*([A-Z][a-zA-Z\s\'&\-\.,]{5,}\s+v\.\s+[A-Z][a-zA-Z\s\'&\-\.,]{5,})$',
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, potential_case_name, re.IGNORECASE)
        if match:
            case_name = match.group(1).strip()
            print(f"\n[SUCCESS] Pattern {i+1} matched!")
            print(f"Extracted: '{case_name}'")
            print(f"Length: {len(case_name)} chars")
            return case_name
    
    print("\n[FAIL] No pattern matched")
    return None

def test_prototype():
    """Test with actual problematic cases from 25-2808.pdf"""
    
    # Load the actual document
    with open("25-2808_full_text.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    print("="*80)
    print("FIX #69 PROTOTYPE TEST")
    print("Testing with actual 25-2808.pdf text")
    print("="*80)
    
    # Test cases: (citation, expected_substring)
    test_cases = [
        ("780 F. Supp. 3d 897", "Cmty. Legal Servs. in E. Palo Alto"),
        ("446 F.3d 167", "Tootle v. Sec"),
        ("56 F.3d 279", "Kidwell v. Dep"),
        ("606 U.S. __", "Noem v. Nat"),
        ("145 S. Ct. 2635", "Trump v. Am"),
    ]
    
    results = []
    
    for citation, expected in test_cases:
        # Find citation in text
        pos = text.find(citation)
        if pos == -1:
            print(f"\n[WARN] Citation '{citation}' not found in document")
            continue
        
        # Extract case name
        extracted = extract_with_comma_anchor(text, citation, pos)
        
        if extracted:
            # Check if expected substring is in extracted
            success = expected.lower() in extracted.lower()
            results.append({
                'citation': citation,
                'extracted': extracted,
                'expected': expected,
                'success': success
            })
        else:
            results.append({
                'citation': citation,
                'extracted': None,
                'expected': expected,
                'success': False
            })
    
    # Print summary
    print("\n" + "="*80)
    print("PROTOTYPE TEST RESULTS")
    print("="*80)
    
    successes = sum(1 for r in results if r['success'])
    total = len(results)
    
    for r in results:
        status = "[OK]" if r['success'] else "[FAIL]"
        print(f"\n{status} {r['citation']}")
        print(f"   Expected: '{r['expected']}'...")
        print(f"   Got:      '{r['extracted']}'")
    
    print(f"\n{'='*80}")
    print(f"SUCCESS RATE: {successes}/{total} ({successes/total*100:.1f}%)")
    print(f"{'='*80}")
    
    if successes >= total * 0.6:  # 60% threshold
        print("\n[SUCCESS] PROTOTYPE SUCCESSFUL - Ready for full implementation!")
        return True
    else:
        print("\n[WARN] PROTOTYPE NEEDS REFINEMENT")
        return False

if __name__ == "__main__":
    success = test_prototype()
    exit(0 if success else 1)

