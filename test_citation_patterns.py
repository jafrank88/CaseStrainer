#!/usr/bin/env python3
"""
Test to check if citation patterns can find the citation in the text
"""

import re

def test_citation_patterns():
    """Test citation patterns"""
    
    text = "Punx v Smithers, 534 F.3d 1290 (1921)"
    citation = "534 F.3d 1290"
    
    print("🔍 Testing citation patterns...")
    print(f"Text: '{text}'")
    print(f"Citation: '{citation}'")
    print("-" * 60)
    
    # Test if citation is in text
    if citation in text:
        print(f"✅ Citation found in text at position: {text.find(citation)}")
    else:
        print(f"❌ Citation not found in text")
    
    # Test common citation patterns
    patterns = [
        r'\b\d+\s+F\.3d\s+\d+\b',
        r'\b\d+\s+F\.\s*3d\s+\d+\b',
        r'\b\d+\s+F\.\s*3rd\s+\d+\b',
        r'\b\d+\s+F\.\s*3D\s+\d+\b',
        r'\b\d+\s+F\.\s*3RD\s+\d+\b',
    ]
    
    for i, pattern in enumerate(patterns, 1):
        matches = re.findall(pattern, text, re.IGNORECASE)
        print(f"Pattern {i}: '{pattern}' -> {len(matches)} matches: {matches}")

if __name__ == "__main__":
    test_citation_patterns() 