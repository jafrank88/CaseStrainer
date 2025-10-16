#!/usr/bin/env python3
"""
Batch analyze proximity between case names and citations in a PDF document.

Usage:
    python batch_case_citation_proximity.py /path/to/file.pdf

Edit the 'pairs' list in the script to specify which (case_name, citation) pairs to check.
"""
import sys
import re
from src.document_processing_unified import extract_text_from_file
from src.case_name_extraction_core import batch_find_case_name_and_citation_proximity, normalize_for_match

# Example pairs to check (edit as needed)
pairs = [
    ("Davison v. State", "195 Wn. 2d 742"),
    ("Davison v. State", "196 Wn. 2d 285"),
    ("Davison v. State", "466 P.3d 231"),
    ("Davison v. State", "466 P.3d 213"),
]

# Improved function to find the closest case name before a citation
CASE_NAME_PATTERNS = [
    r'([A-Z][A-Za-z0-9&.,\'\- \n]{1,100})\s+v\.?\s+([A-Z][A-Za-z0-9&.,\'\- \n]{1,100})(?=,|\s)',
    r'(In\s+re\s+[A-Z][A-Za-z0-9&.,\'\- \n]{1,100})',
    r'(Estate\s+of\s+[A-Z][A-Za-z0-9&.,\'\- \n]{1,100})',
    r'(State\s+v\.?\s+[A-Z][A-Za-z0-9&.,\'\- \n]{1,100})',
    r'(People\s+v\.?\s+[A-Z][A-Za-z0-9&.,\'\- \n]{1,100})',
    r'(United\s+States\s+v\.?\s+[A-Z][A-Za-z0-9&.,\'\- \n]{1,100})',
]

def find_closest_case_name(text, citation):
    norm_citation = normalize_for_match(citation)
    # Find all citation matches (flexible)
    for m in re.finditer(r'.{5,100}', text, re.DOTALL):
        window = m.group(0)
        if normalize_for_match(window).find(norm_citation) != -1:
            citation_start = m.start() + normalize_for_match(window).find(norm_citation)
            # Scan backwards up to 5000 chars
            scan_start = max(0, citation_start - 5000)
            context = text[scan_start:citation_start]
            # Debug: print the last 500 chars of context
            print("\n--- Debug: Last 500 chars before citation ---\n", context[-500:])
            # Improved pattern: allow for newlines and multiple spaces
            pattern = re.compile(
                r'([A-Z][A-Za-z0-9&.,\'\- \n]{1,100})\s+v\.?\s+([A-Z][A-Za-z0-9&.,\'\- \n]{1,100})(?=,|\s)',
                re.DOTALL | re.MULTILINE
            )
            matches = list(pattern.finditer(context))
            if matches:
                last_match = matches[-1]
                print(f"\n--- Debug: Matched case name ---\n{last_match.group(0)} (at context pos {last_match.start()}-{last_match.end()})")
                return last_match.group(0).replace('\n', ' ').strip()
            return None
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_case_citation_proximity.py /path/to/file.pdf")
        sys.exit(1)
    pdf_path = sys.argv[1]
    print(f"Extracting text from: {pdf_path}")
    text = extract_text_from_file(pdf_path)
    print(f"Extracted {len(text)} characters. Running proximity analysis...")
    results = batch_find_case_name_and_citation_proximity(text, pairs)
    for res in results:
        print(f"\nCase: {res['case_name']} | Citation: {res['citation']}")
        if res.get('found', True):
            print(f"  Case name at: {res['case_name_start']}-{res['case_name_end']}")
            print(f"  Citation at: {res['citation_start']}-{res['citation_end']}")
            print(f"  Text between: {repr(res['between_text'])}")
            print(f"  Case name snippet: {repr(res['case_name_snippet'])}")
            print(f"  Citation snippet: {repr(res['citation_snippet'])}")
        else:
            print("  Could not find both case name and citation in the text.")
    # Print the closest case name for 195 Wn. 2d 742
    citation = "195 Wn. 2d 742"
    closest = find_closest_case_name(text, citation)
    print(f"\nClosest case name before '{citation}': {closest if closest else 'Not found'}")

if __name__ == "__main__":
    main() 