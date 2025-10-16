#!/usr/bin/env python
"""Test New Mexico vendor-neutral citation extraction"""
import sys
sys.path.insert(0, 'd:/dev/casestrainer')

# Test text with the NM citation
test_text = """
Hamaatsa, Inc. v. Pueblo of San Felipe, 2017-NM-007, 388 P.3d 977, 985 (2016)
"""

print("=" * 80)
print("TESTING NEW MEXICO VENDOR-NEUTRAL CITATION EXTRACTION")
print("=" * 80)
print(f"\nTest text:\n{test_text}")

# Test with UnifiedCitationProcessorV2
print("\n" + "=" * 80)
print("METHOD 1: UnifiedCitationProcessorV2")
print("=" * 80)

try:
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    import asyncio
    
    processor = UnifiedCitationProcessorV2()
    result = asyncio.run(processor.process_text(test_text))
    
    citations = result.get('citations', [])
    print(f"\n✅ Found {len(citations)} citations:")
    for i, cit in enumerate(citations, 1):
        cit_text = cit.get('citation', 'N/A')
        method = cit.get('method', 'N/A')
        print(f"\n  [{i}] {cit_text}")
        print(f"      Method: {method}")
        print(f"      Extracted Name: {cit.get('extracted_case_name', 'N/A')}")
        
        # Check if it's the vendor-neutral citation
        if '2017-NM-007' in cit_text:
            print(f"      ✅ VENDOR-NEUTRAL CITATION DETECTED!")
        elif '388 P.3d 977' in cit_text:
            print(f"      ✅ REPORTER CITATION DETECTED!")
            
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Also test with basic regex patterns
print("\n" + "=" * 80)
print("METHOD 2: Basic Regex Pattern Test")
print("=" * 80)

import re

# Test vendor-neutral pattern
vendor_neutral_pattern = r'\b\d{4}-[A-Z]{2,4}-\d{3,5}\b'
matches = re.findall(vendor_neutral_pattern, test_text)

print(f"\nVendor-neutral pattern: {vendor_neutral_pattern}")
print(f"Matches found: {matches}")

if matches:
    for match in matches:
        print(f"  ✅ {match}")
else:
    print("  ❌ No matches found")

# Test P.3d pattern
reporter_pattern = r'\b\d{1,4}\s+P\.3d\s+\d{1,4}\b'
reporter_matches = re.findall(reporter_pattern, test_text)

print(f"\nReporter pattern: {reporter_pattern}")
print(f"Matches found: {reporter_matches}")

if reporter_matches:
    for match in reporter_matches:
        print(f"  ✅ {match}")
else:
    print("  ❌ No matches found")

print("\n" + "=" * 80)
print("EXPECTED RESULTS")
print("=" * 80)
print("""
Should extract:
1. Vendor-neutral: 2017-NM-007
2. Reporter: 388 P.3d 977
3. Case name: Hamaatsa, Inc. v. Pueblo of San Felipe
4. Year: 2016
5. Pinpoint: 985

These should be recognized as parallel citations of the same case.
""")
