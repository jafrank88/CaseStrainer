#!/usr/bin/env python3
"""
Test script to verify the improved cluster detection logic
"""

import re

# Test the improved cluster detection
def is_cluster_improved(citation_str):
    # Simple approach: check if it contains commas and looks like a cluster
    # A cluster should have at least one comma and contain multiple citations
    if ',' not in citation_str:
        return False
    
    # Check if it starts with a citation pattern (number + reporter + number)
    # This is more flexible and handles various reporter formats
    parts = citation_str.split(',')
    if len(parts) < 2:
        return False
    
    # The first part should look like a citation (number + reporter + number)
    first_part = parts[0].strip()
    # Check if first part matches citation pattern: number + reporter + number
    citation_pattern = r'^\d+\s+[A-Za-z\.]+\s+\d+$'
    if not re.match(citation_pattern, first_part):
        return False
    
    # At least one other part should be a number or a full citation
    for part in parts[1:]:
        part = part.strip()
        # Check if it's a number or a full citation
        if re.match(r'^\d+$', part) or re.match(r'^\d+\s+[A-Za-z\.]+\s+\d+$', part):
            return True
    
    return False

# Test citations
test_citations = [
    "171 Wn.2d 486, 493, 256 P.3d 321",
    "200 Wn.2d 72, 73, 514 P.3d 643", 
    "347 U.S. 483, 495, 74 S. Ct. 686",
    "171 Wn.2d 486",
    "256 P.3d 321",
    "347 U.S. 483",
    "171 Wn.2d 486, 493",
    "171 Wn.2d 486, 256 P.3d 321"
]

print("Testing improved cluster detection:")
for citation in test_citations:
    is_cluster_result = is_cluster_improved(citation)
    print(f"'{citation}' -> is_cluster: {is_cluster_result}")

print("\nTesting individual parts:")
for citation in test_citations:
    if ',' in citation:
        parts = citation.split(',')
        print(f"\n'{citation}':")
        for i, part in enumerate(parts):
            part = part.strip()
            print(f"  Part {i}: '{part}'")
            
            # Test first part pattern
            if i == 0:
                citation_pattern = r'^\d+\s+[A-Za-z\.]+\s+\d+$'
                matches = bool(re.match(citation_pattern, part))
                print(f"    Matches citation pattern: {matches}")
            
            # Test other parts
            else:
                is_number = bool(re.match(r'^\d+$', part))
                is_citation = bool(re.match(r'^\d+\s+[A-Za-z\.]+\s+\d+$', part))
                print(f"    Is number: {is_number}, Is citation: {is_citation}") 