import re

def extract_case_info(text):
    """Extract case names and years from a legal text with citations."""
    # Pattern to find citations with potential case names
    pattern = r'([A-Z][^.!?]*?\b(?:v\.?|vs\.?|in\s+re|ex\s+rel\.|ex\s+parte)\b[^.!?]*?)(?:,|\()\s*(\d{1,2}\s+[A-Za-z.]+\s+\d+[^)]*(?:\(\d{4}\))?)'
    
    # Find all matches
    matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
    
    results = []
    for match in matches:
        case_name = match.group(1).strip()
        citation = match.group(2).strip()
        
        # Extract year from citation if present
        year_match = re.search(r'\((\d{4})\)', citation)
        year = year_match.group(1) if year_match else None
        
        # Clean up case name
        case_name = re.sub(r'\s+', ' ', case_name)  # Normalize whitespace
        case_name = re.sub(r'[^\w\s.,&\-]', '', case_name)  # Remove special chars
        
        results.append({
            'case_name': case_name,
            'citation': citation,
            'year': year
        })
    
    return results

def main():
    test_text = """We review statutory interpretation de novo. DeSean v. Sanger, 2 Wn. 3d 329, 334-35, 536 P.3d 191 (2023). 
    "The goal of statutory interpretation is to give effect to the legislature's intentions." DeSean, 2 Wn.3d at 335. 
    In determining the plain meaning of a statute, we look to the text of the statute, as well as its No. 87675-9-I/14 14 
    broader context and the statutory scheme as a whole. State v. Ervin, 169 Wn.2d 815, 820, 239 P.3d 354 (2010). 
    Only if the plain text is susceptible to more than one interpretation do we turn to statutory construction, 
    legislative history, and relevant case law to determine legislative intent. Ervin, 169 Wn.2d at 820."""

    print("Extracted Case Information:")
    print("=" * 80)
    
    cases = extract_case_info(test_text)
    for i, case in enumerate(cases, 1):
        print(f"\nCase {i}:")
        print(f"  Name:   {case['case_name']}")
        print(f"  Cite:   {case['citation']}")
        print(f"  Year:   {case['year'] or 'N/A'}")
    
    print("\n" + "=" * 80)
    print("Original Text:")
    print("-" * 80)
    print(test_text)

if __name__ == "__main__":
    main()
