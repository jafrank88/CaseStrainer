#!/usr/bin/env python3
"""
Debug script to test the regex pattern for citation format validation.
"""

import re

def test_citation_regex():
    """Test the citation regex pattern."""
    citation = "John Doe P v. Thurston County, 199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    
    # Regex components
    single_citation = r"\d+\s+[A-Za-z\.]+\s+\d+(?:-\d+)?"
    pinpoint_page = r"\d+(?:-\d+)?"
    citations_group = rf"({single_citation}(?:,\s*{pinpoint_page})*(?:,\s*{single_citation}(?:,\s*{pinpoint_page})*)*)"
    case_name = r"(?:[\w\s\.\'\-]+?,\s*)?"
    year = r"\(\d{4}\)"
    pattern = rf"^{case_name}{citations_group}\s*{year}$"
    
    print(f"Testing citation: {citation}")
    print(f"Pattern: {pattern}")
    print()
    
    # Test each component
    print("Testing single citation pattern:")
    print(f"  Pattern: {single_citation}")
    print(f"  '199 Wn. App. 280': {bool(re.match(single_citation, '199 Wn. App. 280'))}")
    print(f"  '399 P.3d 1195': {bool(re.match(single_citation, '399 P.3d 1195'))}")
    print()
    
    print("Testing pinpoint page pattern:")
    print(f"  Pattern: {pinpoint_page}")
    print(f"  '283': {bool(re.match(pinpoint_page, '283'))}")
    print()
    
    print("Testing case name pattern:")
    print(f"  Pattern: {case_name}")
    print(f"  'John Doe P v. Thurston County, ': {bool(re.match(case_name, 'John Doe P v. Thurston County, '))}")
    print()
    
    print("Testing year pattern:")
    print(f"  Pattern: {year}")
    print(f"  '(2017)': {bool(re.match(year, '(2017)'))}")
    print()
    
    # Test the full pattern
    print("Testing full pattern:")
    match = re.match(pattern, citation)
    print(f"  Match: {bool(match)}")
    if match:
        print(f"  Groups: {match.groups()}")
    
    # Test without case name
    citation_no_name = "199 Wn. App. 280, 283, 399 P.3d 1195 (2017)"
    print(f"\nTesting without case name: {citation_no_name}")
    match = re.match(pattern, citation_no_name)
    print(f"  Match: {bool(match)}")
    if match:
        print(f"  Groups: {match.groups()}")

if __name__ == "__main__":
    test_citation_regex() 