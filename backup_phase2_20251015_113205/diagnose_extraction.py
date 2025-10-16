"""
Diagnose why strict context isolation isn't working.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import PyPDF2
from src.utils.strict_context_isolator import (
    find_all_citation_positions,
    get_strict_context_for_citation,
    extract_case_name_from_strict_context
)

# Load PDF
pdf_path = r'D:\dev\casestrainer\24-2626.pdf'
with open(pdf_path, 'rb') as f:
    pdf = PyPDF2.PdfReader(f)
    text = '\n'.join([page.extract_text() for page in pdf.pages])

print("DIAGNOSTIC: Strict Context Isolation")
print("=" * 100)
print()

# Find all citations
all_positions = find_all_citation_positions(text)
print(f"Found {len(all_positions)} total citations")
print()

# Test specific citations we know are failing
test_citations = [
    ("506 U.S. 139", "P.R. Aqueduct & Sewer Auth. v. Metcalf & Eddy, Inc."),
    ("830 F.3d 881", "Manzari v. Associated Newspapers Ltd."),
    ("304 U.S. 64", "Erie Railroad Co. v. Tompkins"),
]

for cit_text, expected in test_citations:
    print("=" * 100)
    print(f"Testing: {cit_text}")
    print(f"Expected: {expected}")
    print()
    
    # Find position
    pos = text.find(cit_text)
    if pos == -1:
        print(f"ERROR: Citation not found in text")
        continue
    
    # Get strict context
    strict_context = get_strict_context_for_citation(
        text, pos, pos + len(cit_text), all_positions, max_lookback=200
    )
    
    print(f"Strict context ({len(strict_context)} chars):")
    print(f"'{strict_context[-150:]}'")
    print()
    
    # Extract case name
    extracted = extract_case_name_from_strict_context(strict_context, cit_text)
    
    print(f"Extracted: {extracted}")
    print(f"Match: {'YES' if extracted and expected.lower() in extracted.lower() else 'NO'}")
    print()
