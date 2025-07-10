#!/usr/bin/env python3
"""
Test script to fix cluster detection regex pattern
"""

import re

# Test the current cluster detection regex
def is_cluster_current(citation_str):
    pattern = r'\d+\s+[A-Za-z\.]+\s+\d+(,\s*(\d+|\d+\s+[A-Za-z\.]+\s+\d+))+'
    return bool(re.match(pattern, citation_str))

# Test a better pattern
def is_cluster_better(citation_str):
    # More flexible pattern that handles various reporter formats
    pattern = r'\d+\s+[A-Za-z\.]+\s+\d+(,\s*(\d+|\d+\s+[A-Za-z\.]+\s+\d+))+'
    return bool(re.match(pattern, citation_str))

# Test an even more flexible pattern
def is_cluster_flexible(citation_str):
    # Pattern that matches: number + reporter + number, followed by comma + (number OR full citation)
    pattern = r'\d+\s+[A-Za-z\.]+\s+\d+(,\s*(\d+|\d+\s+[A-Za-z\.]+\s+\d+))+'
    return bool(re.match(pattern, citation_str))

# Let's test what the actual issue is
def debug_pattern(citation_str):
    print(f"\nDebugging: '{citation_str}'")
    
    # Test the first part: \d+\s+[A-Za-z\.]+\s+\d+
    first_pattern = r'\d+\s+[A-Za-z\.]+\s+\d+'
    first_match = re.match(first_pattern, citation_str)
    print(f"First part '{first_pattern}' matches: {bool(first_match)}")
    if first_match:
        print(f"  Matches: '{first_match.group(0)}'")
        remaining = citation_str[first_match.end():]
        print(f"  Remaining: '{remaining}'")
        
        # Test the second part on the remaining
        second_pattern = r'(,\s*(\d+|\d+\s+[A-Za-z\.]+\s+\d+))+'
        second_match = re.match(second_pattern, remaining)
        print(f"Second part '{second_pattern}' matches remaining: {bool(second_match)}")
        if second_match:
            print(f"  Matches: '{second_match.group(0)}'")
    else:
        print("  ❌ First part doesn't match")
        # Let's see what we can match
        simple_pattern = r'\d+\s+[A-Za-z\.]+'
        simple_match = re.match(simple_pattern, citation_str)
        print(f"  Simple pattern '{simple_pattern}' matches: {bool(simple_match)}")
        if simple_match:
            print(f"    Matches: '{simple_match.group(0)}'")

# Test citations
test_citations = [
    "171 Wn.2d 486, 493, 256 P.3d 321",
    "200 Wn.2d 72, 73, 514 P.3d 643", 
    "347 U.S. 483, 495, 74 S. Ct. 686",
    "171 Wn.2d 486",
    "256 P.3d 321",
    "347 U.S. 483"
]

print("Testing cluster detection patterns:")
for citation in test_citations:
    current = is_cluster_current(citation)
    better = is_cluster_better(citation)
    flexible = is_cluster_flexible(citation)
    print(f"'{citation}' -> current: {current}, better: {better}, flexible: {flexible}")

# Debug the problematic ones
print("\nDebugging problematic citations:")
for citation in test_citations:
    if not is_cluster_current(citation) and ',' in citation:
        debug_pattern(citation) 