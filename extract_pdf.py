import fitz  # PyMuPDF
import json
import re
from collections import defaultdict

def extract_pdf_metadata(pdf_path):
    """Extract metadata and text from a PDF file with detailed analysis."""
    try:
        doc = fitz.open(pdf_path)
        metadata = dict(doc.metadata)  # Convert to regular dict for JSON serialization
        
        # Initialize analysis structures
        pages_data = []
        all_text = ""
        citation_patterns = [
            r'\b\d+\s+[A-Za-z\.\s]+\d+\b',  # Case citations like "100 Wn.2d 212"
            r'\b\d+\s+[A-Za-z\.\s]+\d+\s+\d{4}\b',  # Citations with year
            r'\b\d+\s+[A-Za-z\.\s]+\d+\s+\(\w+\s+\d{4}\)\b'  # Citations with court and year
        ]
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            all_text += f"\n--- Page {page_num + 1} ---\n{text}"
            
            # Find potential citations
            citations_found = []
            for pattern in citation_patterns:
                citations_found.extend(re.findall(pattern, text))
            
            # Get page dimensions and other metadata
            page_rect = page.rect
            page_data = {
                'page_number': page_num + 1,
                'dimensions': {
                    'width': page_rect.width,
                    'height': page_rect.height
                },
                'text_length': len(text),
                'potential_citations': list(set(citations_found))  # Remove duplicates
            }
            pages_data.append(page_data)
        
        # Document statistics
        stats = {
            'page_count': len(doc),
            'total_text_length': len(all_text),
            'average_page_length': len(all_text) / len(doc) if doc else 0,
            'has_text': len(all_text.strip()) > 0,
            'potential_citation_count': sum(len(p['potential_citations']) for p in pages_data)
        }
        
        # Extract first few lines for content preview
        first_page_text = pages_data[0]['text'] if pages_data and 'text' in pages_data[0] else ""
        first_few_lines = "\n".join(first_page_text.split('\n')[:10]) if first_page_text else ""
        
        doc.close()
        
        return {
            'file_info': {
                'filename': pdf_path.split('\\')[-1],
                'size_bytes': len(open(pdf_path, 'rb').read())
            },
            'metadata': metadata,
            'stats': stats,
            'preview': {
                'first_few_lines': first_few_lines,
                'potential_citations': list(set(c for p in pages_data for c in p['potential_citations']))[:20]  # First 20 unique citations
            },
            'pages_sample': pages_data[:3]  # First 3 pages' data
        }
        
    except Exception as e:
        return {'error': str(e), 'type': type(e).__name__}

if __name__ == "__main__":
    pdf_path = r"D:\\dev\\casestrainer\\wa_briefs\\60179-6.25.pdf"
    result = extract_pdf_metadata(pdf_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
