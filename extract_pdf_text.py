import PyPDF2
import re
import sys

def extract_text_around_citation(pdf_path, citation, context_chars=500):
    """Extract text around a specific citation in a PDF."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                # Look for the citation in the text
                matches = list(re.finditer(re.escape(citation), text, re.IGNORECASE))
                
                if matches:
                    print(f"\n{'='*80}\nFound citation '{citation}' on page {page_num + 1}\n{'='*80}")
                    
                    for match in matches:
                        start = max(0, match.start() - context_chars)
                        end = min(len(text), match.end() + context_chars)
                        context = text[start:end]
                        print(f"\nContext (characters {start}-{end}):\n")
                        print("-" * 80)
                        print(context)
                        print("-" * 80)
                        print("\n\n")
                    
                    return True
            
            print(f"Citation '{citation}' not found in the document.")
            return False
            
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_pdf_text.py <pdf_path> <citation>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    citation = sys.argv[2]
    
    extract_text_around_citation(pdf_path, citation)
