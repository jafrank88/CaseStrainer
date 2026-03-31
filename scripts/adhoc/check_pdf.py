import PyPDF2
import sys

def search_pdf(pdf_path, search_terms):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            print(f"Searching {pdf_path} for terms: {', '.join(search_terms)}\n")
            
            for page_num in range(len(reader.pages)):
                text = reader.pages[page_num].extract_text()
                
                for term in search_terms:
                    if term in text:
                        print(f"\nFound '{term}' on page {page_num + 1}")
                        print("-" * 80)
                        
                        # Show some context around the match
                        pos = text.find(term)
                        start = max(0, pos - 100)
                        end = min(len(text), pos + len(term) + 100)
                        
                        print(f"...{text[start:end]}...")
                        print("-" * 80)
                        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_pdf.py <pdf_path>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    search_terms = ["183 F.3d 1147", "972 F.3d 1058", "Singh-Kaur", "Jibril v. Gonzales", "Singh v. Garland"]
    
    search_pdf(pdf_path, search_terms)
