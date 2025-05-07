#!/usr/bin/env python3
"""
Test script for the briefcheck.py module.
"""

from briefcheck import extract_case_citations

# Test text with a citation
test_text = """
The court in Barnes v. Yahoo!, Inc., 570 F.3d 1096 (9th Cir. 2009) held that 
Section 230 of the Communications Decency Act does not provide immunity for 
promissory estoppel claims.
"""

# Extract citations
citations = extract_case_citations(test_text)

# Print results
print(f"Found {len(citations)} citations:")
for citation in citations:
    print(f"- {citation}")
