import PyPDF2
import sys

pdf_path = r'D:\dev\casestrainer\1034300.pdf'
pdf = PyPDF2.PdfReader(open(pdf_path, 'rb'))

# Extract first 5 pages
for i in range(min(5, len(pdf.pages))):
    print(f"\n{'='*80}\nPAGE {i+1}\n{'='*80}\n")
    print(pdf.pages[i].extract_text())
