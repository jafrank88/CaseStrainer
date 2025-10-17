#!/usr/bin/env python3
"""Test full extraction with context isolation"""
import sys
sys.path.insert(0, 'src')

from src.utils.unified_case_name_extractor import extract_case_name_with_strict_isolation

# Simulate the real problematic text
text = """Upper Skagit Indian Tribe v. Lundgren, 584 U.S. 554, 557, 138 S. Ct. 1649, 200 L. Ed. 2d 931 (2018) (quoting Michigan v. Bay Mills Indian Cmty., 572 U.S. 782, 788, 134 S. Ct. 2024, 188 L. Ed. 2d 1071 (2014))"""

# Find position of "572 U.S. 782"
citation = "572 U.S. 782"
start = text.find(citation)
end = start + len(citation)

print("="*80)
print("FULL EXTRACTION TEST")
print("="*80)
print(f"Text: {text}")
print(f"Citation: {citation}")
print(f"Position: {start}-{end}")
print()

# Test with strict isolation
result = extract_case_name_with_strict_isolation(
    text=text,
    citation_text=citation,
    citation_start=start,
    citation_end=end
)

print(f"Extracted: '{result}'")
print(f"Expected: 'Michigan v. Bay Mills Indian Cmty.'")
print(f"PASS: {'Michigan' in str(result) and 'Bay Mills' in str(result)}")
