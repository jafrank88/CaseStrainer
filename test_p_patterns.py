#!/usr/bin/env python3
"""
Test P.2d and P.3d citation patterns
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_p_patterns():
    """Test P.2d and P.3d citation patterns"""
    
    # Test text with Alaska citations from the PDF
    test_text = """
    See Kelly v. Zamarello, 486 P.2d 906, 911 (Alaska 1971). 
    Also see Grunert v. State, 109 P.3d 924, 929 (Alaska 2005).
    And State v. Dupier, 118 P.3d 1039, 1050 n.62 (Alaska 2005).
    """
    
    print(f"Testing P.2d and P.3d citation patterns...")
    print(f"Test text:\n{test_text}")
    
    processor = UnifiedCitationProcessorV2()
    
    # Test the extraction
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
        
        # Test the patterns directly
        print(f"\n=== Direct Pattern Test ===")
        p2d_pattern = processor.citation_patterns.get('p2d')
        if p2d_pattern:
            matches = list(p2d_pattern.finditer(test_text))
            print(f"P.2d pattern matches: {len(matches)}")
            for match in matches:
                print(f"  - {match.group(0)}")
        
        p3d_pattern = processor.citation_patterns.get('p3d')
        if p3d_pattern:
            matches = list(p3d_pattern.finditer(test_text))
            print(f"P.3d pattern matches: {len(matches)}")
            for match in matches:
                print(f"  - {match.group(0)}")
    
    # Run the async test
    asyncio.run(run_test())

if __name__ == "__main__":
    test_p_patterns()
