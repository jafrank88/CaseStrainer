import PyPDF2
import re

pdf_path = r'D:\dev\casestrainer\1034300.pdf'
pdf = PyPDF2.PdfReader(open(pdf_path, 'rb'))

# Extract all text
full_text = ''.join([page.extract_text() for page in pdf.pages])

# Search for specific citations
citations_to_find = [
    "197 Wn.2d 868",
    "489 P.3d 631", 
    "523 U.S. 751",
    "143 S. Ct. 1689",
    "216 L. Ed. 2d 342",
    "17 F. 4th 901",
    "388 P.3d 977",
    "2017-NM-007"
]

for citation in citations_to_find:
    # Find citation with context
    pattern = re.escape(citation)
    matches = list(re.finditer(pattern, full_text))
    
    if matches:
        print(f"\n{'='*80}")
        print(f"CITATION: {citation}")
        print(f"{'='*80}")
        for match in matches:
            start = max(0, match.start() - 200)
            end = min(len(full_text), match.end() + 100)
            context = full_text[start:end]
            # Clean up whitespace
            context = re.sub(r'\s+', ' ', context)
            print(f"CONTEXT: ...{context}...")
    else:
        print(f"\nNOT FOUND: {citation}")
