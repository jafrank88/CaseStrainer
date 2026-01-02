"""Debug script to understand why N/A extractions are happening."""
import sys
sys.path.insert(0, 'd:/dev/casestrainer/src')

from clean_extraction_pipeline import CleanExtractionPipeline
from unified_case_extraction_master import extract_case_name_and_date_unified_master
from case_name_validator import is_valid_case_name
import requests
import re

# Download PDF text
pdf_url = "https://www.courts.wa.gov/opinions/pdf/1033397.pdf"

# Get text from the PDF (simplified - just get first part)
import pdfplumber
import io

print("Downloading PDF...")
resp = requests.get(pdf_url, timeout=30)
pdf_bytes = io.BytesIO(resp.content)

print("Extracting text...")
with pdfplumber.open(pdf_bytes) as pdf:
    text = ""
    for page in pdf.pages:  # ALL pages
        text += page.extract_text() or ""

print(f"Text length: {len(text)} chars")

# Test citations that are failing
test_citations = [
    ("180 Wn.2d 515", 1667),  # Fisher Broadcasting
    ("179 Wn.2d 376", 1749),  # Sargent
    ("114 Wn.2d 213", 4900),  # City of Seattle v. Rogers
]

print("\n" + "="*60)
print("TESTING EXTRACTION")
print("="*60)

for citation, expected_start in test_citations:
    print(f"\n--- Testing: {citation} (expected start: {expected_start}) ---")
    
    # Find actual position in text
    match = re.search(re.escape(citation), text)
    if match:
        actual_start = match.start()
        actual_end = match.end()
        print(f"  Found at position: {actual_start}-{actual_end}")
        print(f"  Position difference from expected: {actual_start - expected_start}")
        
        # Show context around the citation
        context_start = max(0, actual_start - 100)
        context = text[context_start:actual_start]
        print(f"  Context (100 chars before):")
        print(f"    '{context}'")
        
        # Test master extractor directly
        print(f"\n  Testing master extractor...")
        result = extract_case_name_and_date_unified_master(
            text=text,
            citation=citation,
            start_index=actual_start,
            end_index=actual_end,
            debug=True
        )
        print(f"  Master result: case_name='{result.get('case_name')}', year='{result.get('year')}'")
        
        # Test with eyecite position (to simulate what clean_extraction_pipeline does)
        print(f"\n  Testing with EXPECTED (eyecite) position {expected_start}...")
        result2 = extract_case_name_and_date_unified_master(
            text=text,
            citation=citation,
            start_index=expected_start,
            end_index=expected_start + len(citation),
            debug=True
        )
        print(f"  Master result: case_name='{result2.get('case_name')}', year='{result2.get('year')}'")
        
        # Show context at expected position
        exp_context_start = max(0, expected_start - 100)
        exp_context = text[exp_context_start:expected_start]
        print(f"\n  Context at EXPECTED position:")
        print(f"    '{exp_context}'")
        
    else:
        print(f"  NOT FOUND in text!")
        # Try to find with regex
        pattern = citation.replace(".", r"\.?\s*")
        match2 = re.search(pattern, text)
        if match2:
            print(f"  Found with relaxed pattern at: {match2.start()}")
            print(f"  Matched text: '{match2.group()}'")

print("\n" + "="*60)
print("DONE")
print("="*60)
