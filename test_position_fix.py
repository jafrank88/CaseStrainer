"""Test FIX v8 position correction logic"""
import pdfplumber
import requests
import re
import sys
import importlib
sys.path.insert(0, 'd:/dev/casestrainer')

# Force reload modules to pick up latest changes
import src.utils.strict_context_isolator
importlib.reload(src.utils.strict_context_isolator)

# Download PDF
url = 'https://www.courts.wa.gov/opinions/pdf/1033397.pdf'
response = requests.get(url)
with open('test.pdf', 'wb') as f:
    f.write(response.content)

# Extract text
with pdfplumber.open('test.pdf') as pdf:
    text = ''
    for page in pdf.pages:
        text += page.extract_text() or ''

print(f"Text length: {len(text)}")

# Import extraction function
from src.utils.unified_case_name_extractor import extract_case_name_with_strict_isolation

# Test citations
test_citations = ['180 Wn.2d 515', '179 Wn.2d 376', '114 Wn.2d 213']
for cit in test_citations:
    # Find using regex (what FIX-v8 does)
    cit_pattern = re.escape(cit).replace(r'\ ', r'\s+')
    match = re.search(cit_pattern, text)
    if match:
        actual_start = match.start()
        actual_end = match.end()
        # Show context before citation
        context_start = max(0, actual_start - 80)
        context = text[context_start:actual_start]
        print(f"\n{cit}:")
        print(f"  Position: {actual_start}-{actual_end}")
        print(f"  Context: ...{repr(context[-50:])}")
        
        # Test extraction with corrected position
        extracted = extract_case_name_with_strict_isolation(
            text=text,
            citation_text=cit,
            citation_start=actual_start,
            citation_end=actual_end
        )
        print(f"  EXTRACTED: {extracted}")
    else:
        print(f"\n{cit}: NOT FOUND")
