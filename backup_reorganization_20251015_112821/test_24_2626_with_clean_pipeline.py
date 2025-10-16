"""
Test 24-2626.pdf with the clean extraction pipeline directly.
This bypasses the broken unified_citation_processor_v2.py integration.
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import PyPDF2
from src.clean_extraction_pipeline import extract_citations_clean

print("=" * 100)
print("TESTING 24-2626.PDF WITH CLEAN EXTRACTION PIPELINE")
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
print("Extracting citations...")
citations = extract_citations_clean(text)

print(f"Found {len(citations)} citations")
print()

# Save results
output = {
    'citations': [],
    'total': len(citations)
}

for cit in citations:
    output['citations'].append({
        'citation': cit.citation,
        'extracted_case_name': cit.extracted_case_name,
        'extracted_date': cit.extracted_date,
        'start_index': cit.start_index,
        'end_index': cit.end_index
    })

output_path = r'D:\dev\casestrainer\24-2626_CLEAN_PIPELINE.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print(f"Saved results to: {output_path}")
print()

# Validate against known correct citations
known_correct = {
    "333 F.3d 1018": "Batzel v. Smith",
    "304 U.S. 64": "Erie Railroad Co. v. Tompkins",
    "546 U.S. 345": "Will v. Hallock",
    "506 U.S. 139": "P.R. Aqueduct & Sewer Auth. v. Metcalf & Eddy, Inc.",
    "830 F.3d 881": "Manzari v. Associated Newspapers Ltd.",
    "190 F.3d 963": "United States ex rel. Newsham v. Lockheed Missiles & Space Co.",
    "129 F.4th 1196": "Gopher Media LLC v. Melone",
    "511 U.S. 863": "Digital Equip. Corp. v. Desktop Direct, Inc.",
    "337 U.S. 541": "Cohen v. Beneficial Indus. Loan Corp.",
    "515 U.S. 304": "Johnson v. Jones",
    "558 U.S. 100": "Mohawk Indus., Inc. v. Carpenter",
    "859 F.3d 720": "SolarCity Corp. v. Salt River Project Agric. Improvement & Power Dist.",
    "706 F.3d 1009": "DC Comics v. Pacific Pictures Corp.",
    "736 F.3d 1180": "Makaeff v. Trump Univ., LLC",
    "82 F.4th 785": "Martinez v. ZoomInfo Techs., Inc.",
    "90 F.4th 1042": "Martinez v. ZoomInfo Techs., Inc.",
    "814 F.3d 116": "Ernst v. Carrigan",
    "98 F.4th 1320": "Coomer v. Make Your Life Epic LLC",
    "472 U.S. 511": "Mitchell v. Forsyth",
    "825 F.3d 1043": "Hyan v. Hummer",
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
        
        # Normalize for comparison
        extracted_norm = extracted.lower().replace(',', '').replace('.', '').replace(' ', '')
        expected_norm = expected.lower().replace(',', '').replace('.', '').replace(' ', '')
        
        # Handle abbreviations
        abbreviations = [
            ('company', 'co'),
            ('corporation', 'corp'),
            ('incorporated', 'inc'),
            ('railroad', 'rr'),
        ]
        for full, abbr in abbreviations:
            extracted_norm = extracted_norm.replace(full, abbr)
            expected_norm = expected_norm.replace(full, abbr)
        
        match = expected_norm in extracted_norm or extracted_norm in expected_norm
        
        tested += 1
        if match:
            matches += 1
            status = "PASS"
        else:
            status = "FAIL"
        
        print(f"{status} {cit.citation}")
        print(f"   Expected:  {expected}")
        print(f"   Extracted: {extracted}")
        print()

print("=" * 100)
accuracy = (matches * 100 // tested) if tested > 0 else 0
print(f"ACCURACY: {matches}/{tested} = {accuracy}%")
print("=" * 100)

if matches == tested:
    print()
    print("SUCCESS! Clean pipeline achieves 100% accuracy on 24-2626.pdf!")
elif matches >= tested * 0.8:
    print()
    print(f"GOOD PROGRESS! {matches} correct out of {tested} ({accuracy}%)")
else:
    print()
    print(f"Need more work: {tested - matches} mismatches remaining")
