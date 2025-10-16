#!/usr/bin/env python3
"""Verify that extracted case names and years match the document."""

import sys
import PyPDF2
import re
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def safe_print(text):
    try:
        print(text)
    except:
        print(text.encode('ascii', 'ignore').decode('ascii'))

pdf_path = Path("1033940.pdf")
text = extract_text_from_pdf(pdf_path)

print("="*80)
print("EXTRACTED DATA VERIFICATION")
print("="*80)

# Key citations from the user's output that look suspicious
problem_cases = [
    {
        'citation': '199 Wash.2d 528',
        'production_canonical': 'Branson v. Wash. Fine Wine & Spirits, LLC',
        'production_canonical_date': '2025-09-04',
        'production_extracted': 'American Legion Post No. 32 v. City of Walla Walla',
        'production_extracted_date': '2022',
        'position': 9660
    },
    {
        'citation': '509 P.3d 818',
        'production_canonical': 'Jeffery Moore v. Equitrans, L.P.',
        'production_canonical_date': '2022-02-23',
        'production_extracted': 'American Legion Post No. 32 v. City of Walla Walla',
        'production_extracted_date': '2022',
        'position': 9681
    },
    {
        'citation': '182 Wash.2d 342',
        'production_canonical': 'Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board',
        'production_canonical_date': '2015-01-08',
        'production_extracted': 'State v. Velasquez',
        'production_extracted_date': '2015',
        'position': None  # Need to find
    },
    {
        'citation': '2024 WL 4678268',
        'production_canonical': 'Branson v. Wash. Fine Wine & Spirits, LLC',
        'production_canonical_date': '2025-09-04',
        'production_extracted': 'N/A',
        'production_extracted_date': '2025',
        'position': 37242
    }
]

for case in problem_cases:
    print(f"\n{'='*80}")
    safe_print(f"CITATION: {case['citation']}")
    print(f"{'='*80}")
    
    # Find the citation in the document
    pos = case['position'] if case['position'] else text.find(case['citation'])
    
    if pos == -1:
        # Try without the period
        alt_citation = case['citation'].replace('.', '')
        pos = text.find(alt_citation)
    
    if pos != -1:
        # Get surrounding context
        start = max(0, pos - 300)
        end = min(len(text), pos + 300)
        context = text[start:end]
        
        print(f"\nFOUND IN DOCUMENT at position {pos}:")
        print("-" * 80)
        safe_print(context)
        print("-" * 80)
        
        # Try to extract case name from context
        # Look for "v." pattern before the citation
        before_context = text[max(0, pos-200):pos]
        case_name_pattern = r'([A-Z][A-Za-z\s&,\.\'\-]+?\s+v\.\s+[A-Z][A-Za-z\s&,\.\'\-]+?)[\s,]*(?:\d+)'
        matches = list(re.finditer(case_name_pattern, before_context))
        if matches:
            actual_case_name = matches[-1].group(1).strip()
            safe_print(f"\nACTUAL CASE NAME in document: {actual_case_name}")
        else:
            print(f"\nACTUAL CASE NAME: Could not extract automatically")
        
        # Try to extract year
        year_pattern = r'\((\d{4})\)'
        year_matches = list(re.finditer(year_pattern, context))
        if year_matches:
            actual_year = year_matches[0].group(1)
            print(f"ACTUAL YEAR in document: {actual_year}")
        else:
            print(f"ACTUAL YEAR: Could not find")
        
        print(f"\nPRODUCTION OUTPUT:")
        safe_print(f"  Canonical name: {case['production_canonical']}")
        print(f"  Canonical date: {case['production_canonical_date']}")
        safe_print(f"  Extracted name: {case['production_extracted']}")
        print(f"  Extracted date: {case['production_extracted_date']}")
        
    else:
        print(f"\n❌ NOT FOUND in document!")
        print(f"This citation may not exist or have different formatting")

# Specific checks for the known cases
print(f"\n\n{'='*80}")
print("SPECIFIC CASE ANALYSIS")
print(f"{'='*80}")

print("\n1. Citation '199 Wn.2d 528' (State v. M.Y.G.):")
print("-" * 80)
pos = text.find("199")
if pos != -1:
    context = text[max(0, pos-100):min(len(text), pos+200)]
    safe_print(context)
    print(f"\n✓ Actual case: State v. M.Y.G., 199 Wn.2d 528, 532, 509 P.3d 818 (2022)")
    print(f"✗ Production canonical: Branson v. Wash. Fine Wine & Spirits, LLC, 2025-09-04")
    print(f"✗ Production extracted: American Legion Post No. 32 v. City of Walla Walla, 2022")
    print(f"\n❌ VERIFICATION ERROR: API returned wrong case!")
    print(f"❌ EXTRACTION ERROR: Wrong case name extracted!")

print("\n2. Citation '182 Wash.2d 342' (should be State v. Velasquez?):")
print("-" * 80)
# Search for this citation
search_text = "182 Wn.2d 342"
pos = text.find(search_text)
if pos == -1:
    search_text = "182 Wash.2d 342"  
    pos = text.find(search_text)

if pos != -1:
    context = text[max(0, pos-200):min(len(text), pos+200)]
    safe_print(context)
    print(f"\n✓ Production extracted: State v. Velasquez, 2015")
    print(f"✗ Production canonical: Association of Washington Spirits & Wine Distributors v. Washington State Liquor Control Board, 2015-01-08")
    print(f"\n⚠️ Need to verify which is correct in document")
else:
    print("Citation not found in document")

print(f"\n\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print("\nISSUES IDENTIFIED:")
print("1. ❌ VERIFICATION RETURNING WRONG CASES")
print("   - '199 Wn.2d 528' verifying to 'Branson' (the opinion itself!)")
print("   - Should verify to 'State v. M.Y.G.'")
print("")
print("2. ❌ WRONG CANONICAL DATES")
print("   - Showing '2025-09-04' for citations from 2022")
print("   - Date format seems wrong (YYYY-MM-DD instead of year only)")
print("")
print("3. ❌ EXTRACTION CONTAMINATION STILL PRESENT")
print("   - 'American Legion' appearing when it shouldn't")
print("   - This was supposed to be fixed!")
print("")
print("4. ⚠️ '(Unknown)' DESPITE HAVING DATES")
print("   - Canonical dates are present but marked as 'Unknown'")
print("   - Display issue in frontend?")

