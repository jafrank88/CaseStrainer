"""
Check what case names are extracted for the problematic citations
"""

import sys
import asyncio
sys.path.insert(0, 'D:/dev/casestrainer/src')

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

print("=" * 80)
print("CHECKING EXTRACTED CASE NAMES")
print("=" * 80)

async def check_case_names():
    processor = UnifiedCitationProcessorV2()
    
    # Test text that might contain both citations
    test_text = """
    Doe v. City of New York, 2022 WL 15153410, 855 F.2d 569 (1988).
    """
    
    print("\nTest text:")
    print(test_text)
    
    # Extract citations
    print("\nExtracted citations:")
    result = await processor.process_text(test_text)
    citations = result.get('citations', [])
    
    for i, cit in enumerate(citations):
        print(f"\n{i+1}. Citation: {cit.get('citation', 'N/A')}")
        print(f"   Extracted case name: {cit.get('case_name', 'N/A')}")
        print(f"   Extracted date: {cit.get('date', 'N/A')}")
        print(f"   Context: {cit.get('context', 'N/A')[:100]}...")
    
    # Check if they're being clustered incorrectly
    print("\n" + "=" * 80)
    print("ANALYSIS:")
    print("-" * 40)
    print("If both citations extract the same case name 'Doe v. City of New York',")
    print("they will be incorrectly clustered as parallel citations.")
    print("\nThe issue is likely that:")
    print("1. 2022 WL 15153410 correctly extracts as 'Doe v. City of New York'")
    print("2. 855 F.2d 569 incorrectly extracts as 'Doe v. City of New York' instead of its actual case name")
    print("\nThis causes them to be clustered together despite being completely different cases.")
    print("=" * 80)

# Run the async function
asyncio.run(check_case_names())
