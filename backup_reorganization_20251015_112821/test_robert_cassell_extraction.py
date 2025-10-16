"""
Test case name extraction accuracy against Robert Cassell document.
Compares extracted case names with actual case names in the document.
"""

import sys
import os
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

def find_case_names_in_document(text):
    """
    Manually identify case names in the document by looking for common patterns.
    Returns a dict mapping citation text to expected case name.
    """
    expected_cases = {}
    
    # Pattern to find "In re X" or "X v. Y" followed by citation
    patterns = [
        # In re cases
        r'(In re [A-Z][a-zA-Z\s,\.]+?),\s+(\d+\s+[A-Z]\.[A-Z]\.(?:\s+\d+)?[a-zA-Z]*\.?\s+\d+)',
        # v. cases  
        r'([A-Z][a-zA-Z\s,\.&]+?\s+v\.\s+[A-Z][a-zA-Z\s,\.&]+?),\s+(\d+\s+[A-Z]\.[A-Z]\.(?:\s+\d+)?[a-zA-Z]*\.?\s+\d+)',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            case_name = match.group(1).strip()
            citation = match.group(2).strip()
            # Clean up case name
            case_name = re.sub(r'\s+', ' ', case_name)
            expected_cases[citation] = case_name
    
    return expected_cases

def main():
    print("=" * 80)
    print("CASE NAME EXTRACTION TEST - Robert Cassell Document")
    print("=" * 80)
    
    # Read the document
    doc_path = Path(__file__).parent / 'robert_cassell_doc.txt'
    with open(doc_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"\nDocument size: {len(text)} characters")
    
    # Find expected case names manually
    print("\n" + "-" * 80)
    print("STEP 1: Identifying case names in original document")
    print("-" * 80)
    expected_cases = find_case_names_in_document(text)
    
    print(f"\nFound {len(expected_cases)} citations with case names in document:")
    for citation, case_name in sorted(expected_cases.items()):
        print(f"  {citation:40} -> {case_name}")
    
    # Extract citations using our system
    print("\n" + "-" * 80)
    print("STEP 2: Extracting citations with CaseStrainer")
    print("-" * 80)
    
    processor = UnifiedCitationProcessorV2()
    
    # Use synchronous processing
    import asyncio
    result = asyncio.run(processor.process_text(text))
    
    citations = result.get('citations', [])
    print(f"\nExtracted {len(citations)} citations")
    
    # Compare extracted case names with expected
    print("\n" + "-" * 80)
    print("STEP 3: Comparing extracted vs expected case names")
    print("-" * 80)
    
    matches = 0
    mismatches = 0
    missing = 0
    
    print("\nDetailed comparison:")
    
    # Check each extracted citation
    for cit in citations:
        full_text = cit.get('full_text', '')
        extracted_name = cit.get('extracted_case_name', 'N/A')
        
        # Try to find this citation in our expected cases
        found_expected = None
        for expected_cit, expected_name in expected_cases.items():
            # Check if citation matches (allowing for minor variations)
            if expected_cit in full_text or full_text in expected_cit:
                found_expected = expected_name
                break
        
        if found_expected:
            # Normalize for comparison
            extracted_normalized = re.sub(r'\s+', ' ', extracted_name.strip())
            expected_normalized = re.sub(r'\s+', ' ', found_expected.strip())
            
            if extracted_normalized == expected_normalized:
                print(f"\n  [MATCH] {full_text}")
                print(f"    Extracted: {extracted_name}")
                print(f"    Expected:  {found_expected}")
                matches += 1
            else:
                print(f"\n  [MISMATCH] {full_text}")
                print(f"    Extracted: {extracted_name}")
                print(f"    Expected:  {found_expected}")
                mismatches += 1
        else:
            if extracted_name != 'N/A':
                print(f"\n  [NO REFERENCE] {full_text}")
                print(f"    Extracted: {extracted_name}")
                print(f"    (No expected case name found in document)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_comparisons = matches + mismatches
    if total_comparisons > 0:
        accuracy = (matches / total_comparisons) * 100
        print(f"\nExtracted Citations: {len(citations)}")
        print(f"Expected Case Names Found: {len(expected_cases)}")
        print(f"Successful Matches: {matches}")
        print(f"Mismatches: {mismatches}")
        print(f"Accuracy: {accuracy:.1f}%")
    else:
        print(f"\nNo citations could be compared (no expected case names found)")
    
    print("\n" + "=" * 80)
    
    # Show some examples of extracted citations
    print("\nFirst 5 extracted citations:")
    for i, cit in enumerate(citations[:5], 1):
        print(f"\n{i}. {cit.get('full_text', 'N/A')}")
        print(f"   Case Name: {cit.get('extracted_case_name', 'N/A')}")
        print(f"   Reporter: {cit.get('reporter', 'N/A')}")
        print(f"   Volume: {cit.get('volume', 'N/A')}")
        print(f"   Page: {cit.get('page', 'N/A')}")

if __name__ == '__main__':
    main()
