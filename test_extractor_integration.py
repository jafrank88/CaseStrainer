import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from citation_extractor import CitationExtractor

def test_extractor():
    extractor = CitationExtractor()
    
    # Test case with WL citation
    text = "See Smith v. Jones, 2006 WL 3801910 (W.D. Wash. 2006)"
    
    print(f"Testing text: {text}")
    citations = extractor.extract_citations(text)
    
    print(f"Found {len(citations)} citations")
    
    for i, citation in enumerate(citations, 1):
        print(f"\nCitation {i}:")
        print(f"  Text: {citation.citation}")
        
        # Check if this is a WL citation
        if "WL" in citation.citation:
            print("  This is a WL citation")
            # The citation should be in the format "2006 WL 3801910"
            parts = citation.citation.split()
            if len(parts) >= 3 and parts[1] == "WL":
                print(f"  - Year: {parts[0]}")
                print(f"  - Document number: {parts[2]}")
                return True
    
    print("No WL citation found in the expected format")
    return False

if __name__ == "__main__":
    success = test_extractor()
    if success:
        print("\nWL citation extraction test passed!")
    else:
        print("\nWL citation extraction test failed.")
        sys.exit(1)
