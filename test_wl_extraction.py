import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from citation_extractor import CitationExtractor

def test_wl_extraction():
    extractor = CitationExtractor()
    
    test_texts = [
        "See Smith v. Jones, 2006 WL 3801910 (W.D. Wash. 2006)",
        "In re Doe, 2023 WL 1234567 (9th Cir. 2023)",
        "123 F.3d 456, 460 (9th Cir. 2001) (citing Example v. Test, 2001 WL 1234567)"
    ]
    
    for text in test_texts:
        print(f"\nTesting text: {text}")
        citations = extractor.extract_citations(text)
        print(f"Found {len(citations)} citations")
        
        for i, citation in enumerate(citations, 1):
            print(f"\nCitation {i}:")
            print(f"  Text: {citation.citation}")
            print(f"  Type: {type(citation).__name__}")
            print(f"  Metadata: {citation.metadata}")
            print(f"  Extracted date: {citation.extracted_date}")
            
            # Check if this is a WL citation
            if "WL" in citation.citation:
                print("  This appears to be a WL citation")
                # Try to extract year and document number
                import re
                wl_match = re.search(r'(\d{4})\s+WL\s+(\d+)', citation.citation)
                if wl_match:
                    print(f"  - Year: {wl_match.group(1)}")
                    print(f"  - Document number: {wl_match.group(2)}")

if __name__ == "__main__":
    test_wl_extraction()
