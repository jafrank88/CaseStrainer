#!/usr/bin/env python3
"""
Test U.S. Supreme Court citation extraction
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_us_citations():
    """Test U.S. Supreme Court citation extraction"""
    
    # Test text with the U.S. citations from the PDF
    test_text = """
    Supreme Court No. S-19006    Superior Court No. 3AN-21-05627 CI
    
    O P I N I O N    No. 7788 – September 26, 2025
    
    The Supreme Court has addressed similar issues in 463 U.S. 29 and 390 U.S. 747.
    These cases establish important precedent for environmental regulation.
    """
    
    print(f"Testing U.S. Supreme Court citation extraction...")
    print(f"Test text:\n{test_text}")
    
    processor = UnifiedCitationProcessorV2()
    
    # Test the extraction (async)
    async def run_test():
        result = await processor.process_text(test_text)
        
        print(f"\n=== Results ===")
        citations = result.get('citations', [])
        print(f"Citations found: {len(citations)}")
        
        if citations:
            for i, cit in enumerate(citations):
                print(f"\n{i+1}. Citation:")
                print(f"   Text: {cit.citation}")
                print(f"   Case name: {cit.extracted_case_name}")
                print(f"   Date: {cit.extracted_date}")
                print(f"   Method: {cit.method}")
        else:
            print("No citations found!")
        
        # Test the U.S. pattern directly
        print(f"\n=== Direct Pattern Test ===")
        us_pattern = processor.citation_patterns.get('us')
        if us_pattern:
            matches = list(us_pattern.finditer(test_text))
            print(f"U.S. pattern matches: {len(matches)}")
            for match in matches:
                print(f"  - {match.group(0)}")
        
        us_spaced_pattern = processor.citation_patterns.get('us_spaced')
        if us_spaced_pattern:
            matches = list(us_spaced_pattern.finditer(test_text))
            print(f"U.S. spaced pattern matches: {len(matches)}")
            for match in matches:
                print(f"  - {match.group(0)}")
    
    # Run the async test
    asyncio.run(run_test())

if __name__ == "__main__":
    test_us_citations()
