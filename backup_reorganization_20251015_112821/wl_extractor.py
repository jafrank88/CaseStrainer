import re
from typing import List, Dict, Any, Optional

class WLCitation:
    """Simple class to hold WL citation information."""
    
    def __init__(self, citation_text: str, year: str, doc_number: str, context: str = ""):
        self.citation = citation_text
        self.year = year
        self.doc_number = doc_number
        self.context = context
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy serialization."""
        return {
            'citation': self.citation,
            'year': self.year,
            'document_number': self.doc_number,
            'context': self.context
        }

def extract_wl_citations(text: str, context_window: int = 100) -> List[WLCitation]:
    """
    Extract WL citations from text.
    
    Args:
        text: The text to search for WL citations
        context_window: Number of characters to include before and after the citation for context
        
    Returns:
        List of WLCitation objects
    """
    # Pattern to match WL citations (e.g., 2006 WL 3801910)
    pattern = r'\b(\d{4})\s+WL\s+(\d+)\b'
    
    citations = []
    
    for match in re.finditer(pattern, text):
        year = match.group(1)
        doc_number = match.group(2)
        citation_text = match.group(0)
        
        # Extract context around the citation
        start = max(0, match.start() - context_window)
        end = min(len(text), match.end() + context_window)
        context = text[start:end]
        
        # Create citation object
        citation = WLCitation(
            citation_text=citation_text,
            year=year,
            doc_number=doc_number,
            context=context
        )
        
        citations.append(citation)
    
    return citations

def test_wl_extraction():
    """Test the WL citation extraction."""
    test_cases = [
        "See Smith v. Jones, 2006 WL 3801910 (W.D. Wash. 2006)",
        "In re Doe, 2023 WL 1234567 (9th Cir. 2023)",
        "123 F.3d 456, 460 (9th Cir. 2001) (citing Example v. Test, 2001 WL 1234567)",
        "No WL citation here",
        "Invalid WL 1234567",
        "2006WL3801910"  # No spaces
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest case {i}:")
        print(f"  Text: {text}")
        
        citations = extract_wl_citations(text)
        
        if not citations:
            print("  No WL citations found")
            continue
            
        for j, citation in enumerate(citations, 1):
            print(f"  Citation {j}:")
            print(f"    Full text: {citation.citation}")
            print(f"    Year: {citation.year}")
            print(f"    Document number: {citation.doc_number}")
            print(f"    Context: ...{citation.context}...")

if __name__ == "__main__":
    print("Testing WL citation extraction...")
    test_wl_extraction()
