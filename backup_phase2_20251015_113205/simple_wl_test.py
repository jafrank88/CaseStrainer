import re

def extract_wl_citations(text):
    """Extract WL citations from text using regex."""
    pattern = r'\b(\d{4})\s+WL\s+(\d+)\b'
    return re.finditer(pattern, text)

def test_simple_extraction():
    # Test case with WL citation
    text = "See Smith v. Jones, 2006 WL 3801910 (W.D. Wash. 2006)"
    
    print(f"Testing text: {text}")
    
    # Extract citations using our simple function
    matches = list(extract_wl_citations(text))
    
    if not matches:
        print("No WL citations found")
        return False
    
    print(f"Found {len(matches)} WL citations")
    
    for i, match in enumerate(matches, 1):
        year, doc_number = match.groups()
        print(f"\nCitation {i}:")
        print(f"  Year: {year}")
        print(f"  Document number: {doc_number}")
        print(f"  Full match: {match.group(0)}")
    
    return True

if __name__ == "__main__":
    print("Testing WL citation extraction...")
    success = test_simple_extraction()
    
    if success:
        print("\nTest passed!")
    else:
        print("\nTest failed.")
        import sys
        sys.exit(1)
