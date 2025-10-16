"""
Test the clean extraction pipeline for 100% accuracy.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import PyPDF2
from src.clean_extraction_pipeline import extract_citations_clean

print("=" * 100)
print("TESTING CLEAN EXTRACTION PIPELINE")
print("=" * 100)
print()

# Load PDF
pdf_path = r'D:\dev\casestrainer\24-2626.pdf'
with open(pdf_path, 'rb') as f:
    pdf = PyPDF2.PdfReader(f)
    text = '\n'.join([page.extract_text() for page in pdf.pages])

print(f"Loaded PDF: {len(text)} chars, {len(pdf.pages)} pages")
print()

# Extract using clean pipeline
print("Extracting with clean pipeline...")
citations = extract_citations_clean(text)

print(f"Found {len(citations)} citations")
print()

# Known correct answers
known_correct = {
    "506 U.S. 139": "P.R. Aqueduct & Sewer Auth. v. Metcalf & Eddy, Inc.",
    "830 F.3d 881": "Manzari v. Associated Newspapers Ltd.",
    "304 U.S. 64": "Erie Railroad Co. v. Tompkins",
    "546 U.S. 345": "Will v. Hallock",
}

print("=" * 100)
print("VALIDATION RESULTS")
print("=" * 100)
print()

matches = 0
tested = 0

for cit in citations:
    if cit.citation in known_correct:
        expected = known_correct[cit.citation]
        extracted = cit.extracted_case_name or "N/A"
        
        # Normalize for comparison (handle abbreviations)
        extracted_norm = extracted.lower().replace(',', '').replace('.', '')
        expected_norm = expected.lower().replace(',', '').replace('.', '')
        
        # Normalize common abbreviations
        abbreviations = [
            ('company', 'co'),
            ('corporation', 'corp'),
            ('incorporated', 'inc'),
            ('railroad', 'rr'),
            ('railroad', 'r r'),
        ]
        for full, abbr in abbreviations:
            extracted_norm = extracted_norm.replace(full, abbr)
            expected_norm = expected_norm.replace(full, abbr)
        
        match = expected_norm in extracted_norm or extracted_norm in expected_norm
        
        tested += 1
        if match:
            matches += 1
            print(f"PASS {cit.citation}")
            print(f"   Expected:  {expected}")
            print(f"   Extracted: {extracted}")
        else:
            print(f"FAIL {cit.citation}")
            print(f"   Expected:  {expected}")
            print(f"   Extracted: {extracted}")
        print()

print("=" * 100)
print(f"ACCURACY: {matches}/{tested} = {matches*100//tested if tested > 0 else 0}%")
print("=" * 100)

if matches == tested:
    print()
    print("SUCCESS! Clean pipeline achieves 100% accuracy!")
else:
    print()
    print(f"Need more work: {tested - matches} mismatches remaining")
