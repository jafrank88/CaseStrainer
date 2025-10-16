#!/usr/bin/env python3
"""Test FIX #44: Text normalization before extraction"""

import re
from eyecite import get_citations

# Simulate text with line breaks in citations (like from PDF)
text_with_linebreaks = """
Fraternal Ord. of Eagles, Tenino Aerie No. 564 v. Grand Aerie of Fraternal Ord. of Eagles, 148 Wn.2d  
224, 239, 59 P.3d  655 (2002)
"""

# Test BEFORE normalization (current bug)
print("=" * 80)
print("BEFORE FIX #44: Eyecite on RAW text with line breaks")
print("=" * 80)
eyecite_before = list(get_citations(text_with_linebreaks))
print(f"Citations found: {len(eyecite_before)}")
for cite in eyecite_before:
    print(f"  - {cite.corrected_citation()}")

# Test AFTER normalization (Fix #44)
print("\n" + "=" * 80)
print("AFTER FIX #44: Eyecite on NORMALIZED text")
print("=" * 80)
normalized_text = re.sub(r'\s+', ' ', text_with_linebreaks)
print(f"Normalized text: '{normalized_text[:100]}...'")
eyecite_after = list(get_citations(normalized_text))
print(f"\nCitations found: {len(eyecite_after)}")
for cite in eyecite_after:
    print(f"  - {cite.corrected_citation()}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"Before: {len(eyecite_before)} citations")
print(f"After:  {len(eyecite_after)} citations")
if len(eyecite_after) > len(eyecite_before):
    print(f"✅ FIX #44 WORKS! Recovered {len(eyecite_after) - len(eyecite_before)} missing citations!")
else:
    print(f"❌ No improvement")

