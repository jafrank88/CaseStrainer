#!/usr/bin/env python3

import re

def debug_regex_matching():
    """Debug what the regex patterns are actually matching"""
    
    test_text = """
    Certified questions are questions of law that this court reviews de novo and in light
    of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
    Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
    review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430
    P.3d 655 (2018).
    """
    
    print("🔍 DEBUGGING REGEX MATCHING")
    print("="*80)
    print(f"Test text: {repr(test_text)}")
    print()
    
    # Test the patterns
    citation_patterns = [
        r'\b\d+\s+Wn\.?\s*\d*d\s+\d+\b',  # Washington reports
        r'\b\d+\s+P\.?\s*\d*d\s+\d+\b',   # Pacific reports (single line)
        r'\b\d+\s*\n\s*P\.?\s*\d*d\s+\d+\b',  # Pacific reports (with newline)
        r'\b\d+\s+[A-Z]+\.?\s+\d+\b',     # General format
    ]
    
    for i, pattern in enumerate(citation_patterns):
        print(f"Pattern {i+1}: {pattern}")
        matches = list(re.finditer(pattern, test_text))
        print(f"  Found {len(matches)} matches:")
        for j, match in enumerate(matches):
            print(f"    Match {j+1}: '{match.group(0)}' at position {match.start()}-{match.end()}")
            # Show context around the match
            context_start = max(0, match.start() - 20)
            context_end = min(len(test_text), match.end() + 20)
            context = test_text[context_start:context_end]
            print(f"      Context: {repr(context)}")
        print()

if __name__ == "__main__":
    debug_regex_matching()

