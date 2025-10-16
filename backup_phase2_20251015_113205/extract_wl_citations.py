import re
import PyPDF2
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional
import json

def extract_text_with_fitz(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract text from PDF using PyMuPDF with better text handling."""
    doc = fitz.open(pdf_path)
    pages_data = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        pages_data.append({
            'page_num': page_num + 1,
            'text': text,
            'blocks': [{
                'text': block[4],  # Text content is at index 4
                'bbox': block[:4]  # Bounding box coordinates
            } for block in page.get_text("blocks")]
        })
    
    return pages_data

def find_wl_citations(text: str) -> List[Dict[str, Any]]:
    """Find WL citations in text and return matches with positions."""
    # Pattern to match WL citations with optional punctuation and spaces
    wl_pattern = r'\b(\d+)\s*WL\s*(\d+)\b'
    return [{
        'match': match.group(0),
        'start': match.start(),
        'end': match.end(),
        'volume': match.group(1),
        'page': match.group(2)
    } for match in re.finditer(wl_pattern, text, re.IGNORECASE)]

def extract_wl_citations(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract WL (WestLaw) citations from a PDF file with better context."""
    citations = []
    
    # Extract text from PDF using PyMuPDF for better text handling
    pages_data = extract_text_with_fitz(pdf_path)
    
    for page_data in pages_data:
        text = page_data['text']
        page_num = page_data['page_num']
        
        # Find all WL citations in the page text
        matches = find_wl_citations(text)
        
        for match in matches:
            citation = match['match']
            
            # Get the full paragraph containing the citation
            paragraph_start = text.rfind('\n', 0, match['start']) + 1
            if paragraph_start < 0:
                paragraph_start = 0
                
            paragraph_end = text.find('\n', match['end'])
            if paragraph_end < 0:
                paragraph_end = len(text)
                
            paragraph = text[paragraph_start:paragraph_end].replace('\n', ' ').strip()
            
            # Get surrounding context (200 chars before and after)
            context_start = max(0, match['start'] - 200)
            context_end = min(len(text), match['end'] + 200)
            context = text[context_start:context_end].replace('\n', ' ').strip()
            
            # Try to find case name before the citation
            case_name = None
            preceding_text = text[max(0, match['start'] - 300):match['start']]
            if preceding_text:
                # Look for a case name pattern before the citation
                case_name_match = re.search(r'([A-Z][A-Za-z0-9\s,.]*?)(?=\s*\d+\s*WL\s*\d+)', preceding_text, re.DOTALL)
                if case_name_match:
                    case_name = case_name_match.group(1).strip()
                    # Clean up the case name
                    case_name = re.sub(r'\s+', ' ', case_name).strip()
            
            citations.append({
                'citation': citation,
                'volume': match['volume'],
                'page': match['page'],
                'case_name': case_name,
                'page_num': page_num,
                'paragraph': paragraph,
                'context': f'...{context}...'
            })
    
    return citations

def save_citations_to_file(citations: List[Dict[str, Any]], output_file: str) -> None:
    """Save citations to a JSON file for further analysis."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(citations, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(citations)} citations to {output_file}")

def print_citation(citation: Dict[str, Any], index: int) -> None:
    """Print a single citation in a readable format."""
    print(f"\n{index}. {citation.get('citation', 'N/A')} (Page {citation.get('page_num', 'N/A')})")
    
    if citation.get('case_name'):
        print(f"   Case: {citation['case_name']}")
    
    paragraph = citation.get('paragraph', '')
    if len(paragraph) > 200:
        paragraph = paragraph[:197] + '...'
    print(f"   Context: {paragraph}")

if __name__ == "__main__":
    import sys
    import os
    
    # Set up argument parsing
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    print(f"Processing {os.path.basename(pdf_path)}...")
    
    try:
        # Extract citations
        print("Extracting citations...")
        citations = extract_wl_citations(pdf_path)
        
        if not citations:
            print("No WL citations found in the document.")
            sys.exit(0)
        
        # Save to file for analysis
        output_file = os.path.splitext(pdf_path)[0] + '_citations.json'
        save_citations_to_file(citations, output_file)
        
        # Print summary
        print(f"\nFound {len(citations)} WL citations in {os.path.basename(pdf_path)}:")
        
        # Print first 5 citations with more details
        for i, citation in enumerate(citations[:5], 1):
            print_citation(citation, i)
        
        # Print a few more citations with less detail
        if len(citations) > 5:
            print("\nAdditional citations:")
            for i, citation in enumerate(citations[5:15], 6):
                print(f"   {i}. {citation.get('citation', 'N/A')} (Page {citation.get('page_num', 'N/A')})")
        
        if len(citations) > 15:
            print(f"\n... and {len(citations) - 15} more citations (see {os.path.basename(output_file)} for full list)")
        
        print(f"\nFull results saved to: {os.path.abspath(output_file)}")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError processing {os.path.basename(pdf_path)}: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
