#!/usr/bin/env python3
"""Test the ACTUAL production pipeline (CleanExtractionPipeline)"""
import sys
sys.path.insert(0, 'src')

import requests
from robust_pdf_extractor import extract_pdf_text_robust
from clean_extraction_pipeline import CleanExtractionPipeline

print("Downloading PDF...")
url = "https://www.courts.wa.gov/opinions/pdf/1034300.pdf"
response = requests.get(url)
with open('temp_1034300.pdf', 'wb') as f:
    f.write(response.content)

print("Extracting text from PDF...")
text, method = extract_pdf_text_robust("temp_1034300.pdf")
print(f"Extracted {len(text)} chars using {method}")

print("\nRunning PRODUCTION pipeline (CleanExtractionPipeline)...")
pipeline = CleanExtractionPipeline()
citations = pipeline.extract_citations(text)

print(f"\n{'='*80}")
print(f"EXTRACTION RESULTS: {len(citations)} citations found")
print(f"{'='*80}\n")

# Find and show the Hamaatsa citations
hamaatsa_citations = []
for cit in citations:
    if "388 P.3d 977" in cit.citation or "2017-NM-007" in cit.citation:
        hamaatsa_citations.append(cit)
        print(f"FOUND: {cit.citation}")
        print(f"   Case name: {cit.extracted_case_name}")
        print(f"   Year: {cit.extracted_date}")
        print()

if not hamaatsa_citations:
    print("Hamaatsa citations not found!")
else:
    print(f"\n{'='*80}")
    print(f"HAMAATSA RESULTS:")
    print(f"{'='*80}")
    for cit in hamaatsa_citations:
        print(f"{cit.citation}: {cit.extracted_case_name} ({cit.extracted_date})")
