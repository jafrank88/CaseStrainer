#!/usr/bin/env python3
"""
Test the complete fix for Washington citations with pinpoint pages
"""

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

async def test_extraction():
    """Test the extraction with the fix"""
    
    processor = UnifiedCitationProcessorV2()
    
    # Test text from the document
    text = """When assessing the truth or falsity of a communication, the words uttered by the broadcaster should be construed in the sense in which the ordinary person would understand them in their context.  Amsbury v. Cowles Publishing Company, 76 Wn.2d 733, 458 P.2d 882 (1969); Jha v. Khan, 24 Wn. App. 2d 377, 392, 520 P.3d 470 (2022); Exner v. American Medical Association, 12 Wn. App. 215, 217 (1974)."""
    
    print("Testing citation extraction with pinpoint pages:")
    print(f"Text: {text}")
    print()
    
    # Extract citations using async
    result = await processor.process_citations_unified(text)
    
    print(f"Found {len(result)} citations:")
    for i, cit in enumerate(result):
        print(f"\n{i+1}. {cit.citation}")
        print(f"   Method: {cit.method}")
        print(f"   Pattern: {cit.pattern}")
        if hasattr(cit, 'extracted_case_name') and cit.extracted_case_name:
            print(f"   Case: {cit.extracted_case_name}")
        if hasattr(cit, 'pinpoint_pages') and cit.pinpoint_pages:
            print(f"   Pinpoint pages: {cit.pinpoint_pages}")
        if hasattr(cit, 'parallel_citations') and cit.parallel_citations:
            print(f"   Parallel citations: {cit.parallel_citations}")
    
    # Check if Jha v. Khan is extracted as one citation
    jha_citations = [c for c in result if 'Jha v. Khan' in str(getattr(c, 'extracted_case_name', ''))]
    print(f"\nFound {len(jha_citations)} Jha v. Khan citations:")
    for cit in jha_citations:
        print(f"  - {cit.citation}")
        if cit.pinpoint_pages:
            print(f"    Pinpoint: {cit.pinpoint_pages}")
        if cit.parallel_citations:
            print(f"    Parallel: {cit.parallel_citations}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
