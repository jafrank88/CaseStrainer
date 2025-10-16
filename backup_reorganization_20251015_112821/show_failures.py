"""
Show the specific failures from the 24-2626 test.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import PyPDF2
from src.clean_extraction_pipeline import extract_citations_clean

# Load PDF
pdf_path = r'D:\dev\casestrainer\24-2626.pdf'
with open(pdf_path, 'rb') as f:
    pdf = PyPDF2.PdfReader(f)
    text = '\n'.join([page.extract_text() for page in pdf.pages])

citations = extract_citations_clean(text)

# Known failures
failures = {
    "511 U.S. 863": "Digital Equip. Corp. v. Desktop Direct, Inc.",
    "558 U.S. 100": "Mohawk Indus., Inc. v. Carpenter",
    "90 F.4th 1042": "Martinez v. ZoomInfo Techs., Inc.",
}

print("FAILING CASES - DETAILED ANALYSIS")
print("=" * 100)
print()

for cit in citations:
    if cit.citation in failures:
        expected = failures[cit.citation]
        extracted = cit.extracted_case_name or "N/A"
        
        print(f"Citation: {cit.citation}")
        print(f"Expected:  {expected}")
        print(f"Extracted: {extracted}")
        print(f"Position:  {cit.start_index}-{cit.end_index}")
        
        # Show context
        if cit.start_index:
            context_start = max(0, cit.start_index - 150)
            context_end = cit.start_index
            context = text[context_start:context_end]
            print(f"Context (150 chars before citation):")
            print(f"  ...{context[-150:]}")
        
        print()
        print("-" * 100)
        print()
