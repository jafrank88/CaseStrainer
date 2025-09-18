import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from citation_extractor import CitationExtractor

def test_integrated_wl_extraction():
    """Test the integrated WL citation extraction."""
    extractor = CitationExtractor()
    
    test_cases = [
        "See Smith v. Jones, 2006 WL 3801910 (W.D. Wash. 2006)",
        "In re Doe, 2023 WL 1234567 (9th Cir. 2023)",
        "123 F.3d 456, 460 (9th Cir. 2001) (citing Example v. Test, 2001 WL 1234567)"
    ]
    
    print("Testing integrated WL citation extraction...")
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {text}")
        
        citations = extractor.extract_citations(text)
        wl_citations = [c for c in citations if "WL" in c.citation]
        
        print(f"Found {len(citations)} total citations, {len(wl_citations)} WL citations")
        
        for j, citation in enumerate(wl_citations, 1):
            print(f"  WL Citation {j}:")
            print(f"    Text: {citation.citation}")
            print(f"    Year: {citation.extracted_date}")
            print(f"    Source: {citation.source}")
            print(f"    Confidence: {citation.confidence}")
            if citation.metadata:
                print(f"    Type: {citation.metadata.get('citation_type')}")
                print(f"    Doc Number: {citation.metadata.get('document_number')}")

if __name__ == "__main__":
    test_integrated_wl_extraction()
