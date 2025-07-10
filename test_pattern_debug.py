#!/usr/bin/env python3
"""
Simple test to debug the regex pattern directly
"""

import re

def test_pattern_directly():
    """Test the regex pattern directly"""
    
    context = "Punx v Smithers, "
    print(f"Context: '{context}'")
    print(f"Context length: {len(context)}")
    print(f"Context bytes: {context.encode('utf-8')}")
    print(f"Context repr: {repr(context)}")
    print("-" * 50)
    
    # Check what's between "Punx" and "Smithers"
    punx_index = context.find("Punx")
    smithers_index = context.find("Smithers")
    if punx_index != -1 and smithers_index != -1:
        between_text = context[punx_index:smithers_index + len("Smithers")]
        print(f"Text from 'Punx' to 'Smithers': '{between_text}'")
        print(f"Between 'Punx' and 'Smithers': '{context[punx_index + 4:smithers_index]}'")
        print(f"ASCII codes: {[ord(c) for c in context[punx_index + 4:smithers_index]]}")
    
    # Test the simple pattern
    pattern = r'([A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+)\s*[,;:.]?'
    print(f"\nPattern: {pattern}")
    
    matches = list(re.finditer(pattern, context, re.IGNORECASE))
    print(f"Matches: {len(matches)}")
    for i, match in enumerate(matches):
        print(f"  Match {i+1}: '{match.group(1)}'")
    
    # Test with a very simple pattern
    pattern_simple = r'Punx v Smithers'
    print(f"\nSimple pattern: {pattern_simple}")
    
    matches_simple = list(re.finditer(pattern_simple, context))
    print(f"Matches: {len(matches_simple)}")
    for i, match in enumerate(matches_simple):
        print(f"  Match {i+1}: '{match.group(0)}'")
    
    # Test with just the v. part
    pattern_v = r'v\.'
    print(f"\nV pattern: {pattern_v}")
    
    matches_v = list(re.finditer(pattern_v, context))
    print(f"Matches: {len(matches_v)}")
    for i, match in enumerate(matches_v):
        print(f"  Match {i+1}: '{match.group(0)}' at position {match.start()}")

if __name__ == "__main__":
    test_pattern_directly() 