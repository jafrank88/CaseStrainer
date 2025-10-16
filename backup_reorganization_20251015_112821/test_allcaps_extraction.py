"""
Test script to verify all-caps case name extraction works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.citation_extractor import CitationExtractor
from src.unified_case_extraction_master import UnifiedCaseExtractionMaster

def test_allcaps_extraction():
    """Test extraction of all-caps case names from the court document."""
    
    # Read the test file
    with open('25-2808_full_text.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    
    print("=" * 80)
    print("TESTING ALL-CAPS CASE NAME EXTRACTION")
    print("=" * 80)
    
    # Test with CitationExtractor
    print("\n1. Testing CitationExtractor...")
    extractor = CitationExtractor()
    citations = extractor.extract_citations(text, use_eyecite=False)
    
    print(f"   Found {len(citations)} citations")
    for i, citation in enumerate(citations[:5], 1):  # Show first 5
        print(f"   {i}. {citation.citation}")
        if citation.extracted_case_name:
            print(f"      Case name: {citation.extracted_case_name}")
        if citation.extracted_date:
            print(f"      Year: {citation.extracted_date}")
    
    # Test with UnifiedCaseExtractionMaster
    print("\n2. Testing UnifiedCaseExtractionMaster...")
    master = UnifiedCaseExtractionMaster()
    
    # Look for the specific case name in the document
    test_cases = [
        "CMTY. LEGAL SERVICES V . U.S.  HHS",
        "Cmty. Legal Servs. in E. Palo Alto v. U.S. Dep't of Health & Hum. Servs.",
        "137 F.4th 932",
    ]
    
    for test_case in test_cases:
        print(f"\n   Searching for: '{test_case}'")
        if test_case in text:
            # Find position
            pos = text.find(test_case)
            context_start = max(0, pos - 100)
            context_end = min(len(text), pos + len(test_case) + 100)
            context = text[context_start:context_end]
            
            print(f"   Found at position {pos}")
            print(f"   Context: ...{context}...")
            
            # Try to extract case name
            result = master.extract_case_name_and_date(
                text=text,
                citation=test_case,
                start_index=pos,
                end_index=pos + len(test_case)
            )
            
            if result:
                print(f"   ✓ Extracted case name: {result.case_name}")
                print(f"   ✓ Extracted year: {result.year}")
                print(f"   ✓ Method: {result.method}")
                print(f"   ✓ Confidence: {result.confidence}")
            else:
                print(f"   ✗ Failed to extract case name")
        else:
            print(f"   Not found in text")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_allcaps_extraction()
