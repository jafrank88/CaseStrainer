#!/usr/bin/env python3
"""
Test script to debug cluster detection regex pattern
"""

import re

# Test the cluster detection regex
def is_cluster(citation_str):
    # Match: full citation, then comma, then either a number or another full citation
    pattern = r'\d+\s+[A-Za-z\.]+\s+\d+(,\s*(\d+|\d+\s+[A-Za-z\.]+\s+\d+))+'
    return bool(re.match(pattern, citation_str))

# Test citations
test_citations = [
    "171 Wn.2d 486, 493, 256 P.3d 321",
    "200 Wn.2d 72, 73, 514 P.3d 643", 
    "347 U.S. 483, 495, 74 S. Ct. 686",
    "171 Wn.2d 486",
    "256 P.3d 321",
    "347 U.S. 483"
]

print("Testing cluster detection:")
for citation in test_citations:
    is_cluster_result = is_cluster(citation)
    print(f"'{citation}' -> is_cluster: {is_cluster_result}")

print("\nTesting regex pattern step by step:")
pattern = r'\d+\s+[A-Za-z\.]+\s+\d+(,\s*(\d+|\d+\s+[A-Za-z\.]+\s+\d+))+'
test_citation = "171 Wn.2d 486, 493, 256 P.3d 321"

print(f"Pattern: {pattern}")
print(f"Test citation: {test_citation}")

match = re.match(pattern, test_citation)
if match:
    print(f"✅ Match found: {match.group(0)}")
    print(f"Groups: {match.groups()}")
else:
    print("❌ No match found")
    
    # Let's break down the pattern
    print("\nBreaking down the pattern:")
    
    # First part: \d+\s+[A-Za-z\.]+\s+\d+
    first_part = r'\d+\s+[A-Za-z\.]+\s+\d+'
    first_match = re.match(first_part, test_citation)
    print(f"First part '{first_part}' matches: {bool(first_match)}")
    if first_match:
        print(f"  Matches: '{first_match.group(0)}'")
    
    # Second part: (,\s*(\d+|\d+\s+[A-Za-z\.]+\s+\d+))+
    second_part = r'(,\s*(\d+|\d+\s+[A-Za-z\.]+\s+\d+))+'
    # Test on the remaining part after first match
    if first_match:
        remaining = test_citation[first_match.end():]
        print(f"Remaining after first match: '{remaining}'")
        second_match = re.match(second_part, remaining)
        print(f"Second part '{second_part}' matches remaining: {bool(second_match)}")
        if second_match:
            print(f"  Matches: '{second_match.group(0)}'") 