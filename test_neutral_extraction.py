"""
Test if neutral citations are being extracted.
"""
import sys
import os
sys.path.insert(0, '/app')  # For Docker environment
os.chdir('/app')

# Set up logging
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Import the processor
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

text = "Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977 (2016)"

print("=" * 70)
print("TESTING NEUTRAL CITATION EXTRACTION")
print("=" * 70)
print(f"\nTest text:\n{text}\n")

processor = UnifiedCitationProcessorV2()

# Check if the pattern exists
print("Checking citation patterns...")
if 'neutral_nm' in processor.citation_patterns:
    print("✅ neutral_nm pattern exists")
    pattern = processor.citation_patterns['neutral_nm']
    import re
    matches = list(pattern.finditer(text))
    if matches:
        print(f"✅ Pattern matches: {[m.group() for m in matches]}")
    else:
        print("❌ Pattern doesn't match the text")
else:
    print("❌ neutral_nm pattern NOT found")

print("\n" + "=" * 70)
print("Running full extraction pipeline...")
print("=" * 70 + "\n")

# Run extraction
import asyncio
result = asyncio.run(processor.process_text(text))

citations = result.get('citations', [])
print(f"\nTotal citations extracted: {len(citations)}")

for i, cit in enumerate(citations, 1):
    if hasattr(cit, 'citation'):
        cit_text = cit.citation
        extracted_name = getattr(cit, 'extracted_case_name', 'N/A')
    elif isinstance(cit, dict):
        cit_text = cit.get('citation', 'N/A')
        extracted_name = cit.get('extracted_case_name', 'N/A')
    else:
        cit_text = str(cit)
        extracted_name = 'N/A'
    
    print(f"\nCitation {i}: {cit_text}")
    print(f"  Extracted case name: {extracted_name}")

print("\n" + "=" * 70)
print("ANALYSIS:")
print("=" * 70)

nm_found = any(('2017-NM-007' in (getattr(c, 'citation', '') if hasattr(c, 'citation') else c.get('citation', ''))) for c in citations)
p3d_found = any(('388 P.3d 977' in (getattr(c, 'citation', '') if hasattr(c, 'citation') else c.get('citation', ''))) for c in citations)

print(f"✅ 2017-NM-007 extracted: {nm_found}")
print(f"✅ 388 P.3d 977 extracted: {p3d_found}")

if nm_found and p3d_found:
    print("\n✅ SUCCESS: Both citations extracted")
else:
    print("\n❌ FAILURE: Missing citation(s)")
