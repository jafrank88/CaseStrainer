#!/usr/bin/env python3
"""
Test the pattern matching directly
"""

import re

def test_pattern_matching():
    """Test how the patterns match the citations"""
    
    # All patterns from the processor
    patterns = {
        "wash_with_pinpoint_and_parallel": re.compile(
            r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*(?:App\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+))?(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b",
            re.IGNORECASE,
        ),
        "parallel_citation_cluster": re.compile(
            r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)(?:\s*,\s*(\d+)\s+(?:P\.3d|P\.2d)\s+(\d+))?\s*(?:\(\d{4}\))?\b",
            re.IGNORECASE,
        ),
        "simple_wash2d": re.compile(r"\b(\d+)\s+(?:Wash\.|Wn\.)\s*2d\s+(\d+)\b", re.IGNORECASE),
        "simple_p3d": re.compile(r"\b(\d+)\s+P\.3d\s+(\d+)\b", re.IGNORECASE),
        "wn_app": re.compile(r"\b(\d+)\s+Wn\.?\s*App\.?\s+(\d+)\b", re.IGNORECASE),
    }
    
    # Test text
    text = """Jha v. Khan, 24 Wn. App. 2d 377, 392, 520 P.3d 470 (2022)"""
    
    print("Testing pattern matching:")
    print(f"Text: {text}")
    print()
    
    # Test each pattern
    for name, pattern in patterns.items():
        matches = list(pattern.finditer(text))
        print(f"{name}:")
        for match in matches:
            print(f"  Match: '{match.group(0)}' at {match.start()}-{match.end()}")
            if match.groups():
                print(f"  Groups: {match.groups()}")
        if not matches:
            print("  No matches")
        print()
    
    # Test what happens with simple patterns
    print("Testing simple patterns on individual citations:")
    
    test_citations = [
        "24 Wn. App. 2d 377",
        "520 P.3d 470",
        "24 Wn. App. 2d 377, 392, 520 P.3d 470",
    ]
    
    for cit in test_citations:
        print(f"\nCitation: {cit}")
        for name, pattern in patterns.items():
            if pattern.search(cit):
                print(f"  Matches: {name}")

if __name__ == "__main__":
    test_pattern_matching()
