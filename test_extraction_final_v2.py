import re

def print_header(text):
    print("\n" + "=" * 80)
    print(f"{text:^80}")
    print("=" * 80)

def extract_case_info(text):
    # First, find all citations with years
    citation_pattern = r'([A-Z][^.!?]*?\b(?:v\.?|vs\.?|in\s+re|ex\s+rel\.|ex\s+parte)\b[^.!?]*?)(?:,|\()\s*((?:\d+\s+[A-Za-z.]+\s+\d+[^)]*(?:\(\d{4}\))?)|(?:\d+\s+[A-Za-z.]+\s+at\s+\d+))'
    
    matches = list(re.finditer(citation_pattern, text, re.IGNORECASE | re.DOTALL))
    
    if not matches:
        print("No citations found in the text.")
        return []
    
    results = []
    
    for i, match in enumerate(matches, 1):
        case_name = match.group(1).strip()
        citation = match.group(2).strip()
        
        # Extract year from citation if present
        year_match = re.search(r'\((\d{4})\)', citation)
        year = year_match.group(1) if year_match else None
        
        # If no year in citation, try to find it in the surrounding text
        if not year:
            # Look for year in the next 50 characters after the citation
            next_text = text[match.end():match.end()+50]
            year_match = re.search(r'(?:\b(?:19|20)\d{2}\b)', next_text)
            if year_match:
                year = year_match.group(0)
        
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

    print_header("EXTRACTION TEST RESULTS")
    
    cases = extract_case_info(test_text)
    
    if not cases:
        print("No cases were extracted from the text.")
        return
    
    print(f"\nFound {len(cases)} case(s) in the text:\n")
    
    for i, case in enumerate(cases, 1):
        print(f"CASE {i}:")
        print(f"  Name:   {case['case_name']}")
        print(f"  Cite:   {case['citation']}")
        print(f"  Year:   {case['year'] or 'N/A'}")
        print()
    
    print_header("ORIGINAL TEXT")
    print(test_text)

if __name__ == "__main__":
    # Force flush output
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {str(e)}", file=sys.stderr)
