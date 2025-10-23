"""
Phase 6 Debug: Single citation test to see debug logs
"""

import sys
sys.path.insert(0, '/app')

import asyncio
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Test with pinpoint citations (", 221" and ", 157") - this is the original problem format
test_text = """See Cayuga Indian Nation v. Seneca County, 761 F.3d 218, 221 (2d Cir. 2014); Oneida Indian Nation v. Madison County, 605 F.3d 149, 157 (2d Cir. 2010); Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977, 985 (2016)."""

async def test():
    processor = UnifiedCitationProcessorV2()
    result = await processor.process_text(text=test_text)
    
    citations = result.get('citations', [])
    
    print(f"\n{len(citations)} citations found")
    for cit in citations:
        print(f"  {cit.citation}: {cit.extracted_case_name}")

if __name__ == '__main__':
    asyncio.run(test())
