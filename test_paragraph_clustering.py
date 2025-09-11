#!/usr/bin/env python3
"""
Test the improved case name extraction with the exact paragraph from the user
"""

import asyncio
from src.unified_case_name_extractor import extract_case_name_and_date_unified

async def test_paragraph_extraction():
    """Test case name extraction for the exact paragraph"""
    
    # Exact paragraph from the user
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""

    # Test citations from the paragraph
    test_citations = [
        "178 Wn. App. 929",  # Knight case
        "317 P.3d 1068",     # Knight case
        "188 Wn.2d 114",     # Black case
        "392 P.3d 1041",     # Black case
        "155 Wn. App. 715",  # Blackmon case
        "230 P.3d 233"       # Blackmon case
    ]

    print("Testing case name extraction for the exact paragraph:")
    print("=" * 80)
    print(f"Text: {test_text[:100]}...")
    print("=" * 80)

    for i, citation in enumerate(test_citations, 1):
        print(f"\n{i}. Testing citation: {citation}")
        
        # Find the citation in the text
        citation_start = test_text.find(citation)
        if citation_start == -1:
            print(f"   ❌ Citation not found in text")
            continue
        
        citation_end = citation_start + len(citation)
        
        # Extract case name and date
        result = extract_case_name_and_date_unified(
            text=test_text,
            citation=citation,
            citation_start=citation_start,
            citation_end=citation_end
        )
        
        print(f"   📍 Position: {citation_start}-{citation_end}")
        print(f"   🏷️  Case Name: '{result.get('case_name', 'N/A')}'")
        print(f"   📅 Date: '{result.get('date', 'N/A')}'")
        print(f"   📅 Year: '{result.get('year', 'N/A')}'")
        print(f"   🎯 Method: {result.get('method', 'N/A')}")
        print(f"   💯 Confidence: {result.get('confidence', 'N/A')}")
        
        if result.get('debug_info'):
            debug = result['debug_info']
            print(f"   🔍 Debug: context_length={debug.get('context_length', 'N/A')}")

    print("\n" + "=" * 80)
    print("Expected Results:")
    print("1. Knight case: 'In re Vulnerable Adult Petition for Knight' (2014)")
    print("2. Black case: 'In re Marriage of Black' (2017)")
    print("3. Blackmon case: 'Blackmon v. Blackmon' (2010)")
    print("=" * 80)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_paragraph_extraction())



