import re
import sys

def extract_case_name(text, citation_text, start_pos):
    """Extract case name from text around a citation."""
    print(f"\nExtracting case name for: {citation_text}")
    
    # Look back 100 characters before the citation
    context_start = max(0, start_pos - 100)
    context = text[context_start:start_pos]
    
    print(f"Context before citation: ...{context[-100:]}")
    
    # Pattern 1: Look for case name followed by citation
    pattern1 = r'([A-Z][^.!?]*?\b(?:v\.?|vs\.?|in\s+re|ex\s+rel\.|ex\s+parte)\b[^.!?]*?)[,.]\s*' + re.escape(citation_text)
    
    # Pattern 2: Look for case name in previous sentence
    pattern2 = r'([A-Z][^.!?]*?\b(?:v\.?|vs\.?|in\s+re|ex\s+rel\.|ex\s+parte)\b[^.!?]*?)[.!?]'
    
    for pattern in [pattern1, pattern2]:
        print(f"\nTrying pattern: {pattern}")
        match = re.search(pattern, text[:start_pos + 100], re.IGNORECASE | re.DOTALL)
        if match:
            case_name = match.group(1).strip()
            # Clean up the case name
            case_name = re.sub(r'\s+', ' ', case_name)
            case_name = re.sub(r'^[^A-Za-z]+', '', case_name)
            print(f"✅ Found match: {case_name}")
            return case_name
    
    print("❌ No case name found")
    return None

def main():
    test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023). 
    "The goal of statutory interpretation is to give effect to the legislature's intentions." DeSean, 2 Wn.3d at 335. 
    In determining the plain meaning of a statute, we look to the text of the statute, as well as its No. 87675-9-I/14 14 
    broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010). 
    Only if the plain text is susceptible to more than one interpretation do we turn to statutory construction, 
    legislative history, and relevant case law to determine legislative intent. Ervin, 169 Wn.2d at 820."""

    test_cases = [
        {"text": "2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023)", "pos": test_text.find("2 Wn. 3d 329")},
        {"text": "DeSean, 2 Wn.3d at 335", "pos": test_text.find("DeSean, 2 Wn.3d at 335")},
        {"text": "169 Wn.2d 815, 820, 239 P.3d 354 (2010)", "pos": test_text.find("169 Wn.2d 815")},
        {"text": "Ervin, 169 Wn.2d at 820", "pos": test_text.find("Ervin, 169 Wn.2d at 820")}
    ]
    
    print("Case Name Extraction Test\n" + "="*50)
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest {i}:")
        print("-" * 50)
        case_name = extract_case_name(test_text, case["text"], case["pos"])
        print(f"\nResult for '{case['text']}': {case_name or 'Not found'}")
        print("=" * 50)

if __name__ == "__main__":
    main()
