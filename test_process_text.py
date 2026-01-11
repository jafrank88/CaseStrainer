"""
Test to check what's happening in process_text
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

async def test_process_text():
    print("Creating processor...")
    processor = UnifiedCitationProcessorV2()
    
    test_text = "Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988)."
    
    print("\nCalling process_text...")
    result = await processor.process_text(test_text)
    
    print(f"\nResults: {len(result.get('citations', []))} citations")
    for cit in result.get('citations', []):
        print(f"  - {cit.citation}: {cit.extracted_case_name}")

# Run the test
asyncio.run(test_process_text())
