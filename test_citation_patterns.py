#!/usr/bin/env python3
"""
Test citation patterns for Washington state reporters.
"""

import re

def test_washington_citation_patterns():
    """Test Washington state citation patterns."""
    print("=" * 80)
    print("TESTING WASHINGTON CITATION PATTERNS")
    print("=" * 80)
    
    # Test cases with various spacing and formatting
    test_cases = [
        # Wn patterns
        "123Wn.2d456",
        "123 Wn.2d 456",
        "123Wn.2d 456",
        "123 Wn.2d456",
        "123-Wn.-2d-456",
        "123Wn2d456",
        "123 Wn 2d 456",
        "123WnApp456",
        "123 Wn. App. 456",
        "123WnApp 456",
        "123 WnApp456",
        
        # Wash patterns
        "123Wash.2d456",
        "123 Wash.2d 456",
        "123Wash.2d 456",
        "123 Wash.2d456",
        "123-Wash.-2d-456",
        "123Wash2d456",
        "123 Wash 2d 456",
        "123WashApp456",
        "123 Wash. App. 456",
        "123WashApp 456",
        "123 WashApp456",
        
        # With different series
        "123Wn.3d456",
        "123 Wn.4th 456",
        "123Wash.3d 456",
        "123 Wash.4th 456"
    ]
    
    # Base patterns for Washington state reporters
    wn_patterns = [
        # Wn.2d, Wn.3d, Wn.4th, etc.
        r'(\d+)[\s-]*(Wn\.?)[\s-]*(2d|3d|4th|App\.?|\d+)[\s-]*(\d+)',
        # Wn (no series)
        r'(\d+)[\s-]*(Wn\.?)[\s-]*(\d+)',
    ]
    
    # Washington patterns (full word)
    wash_patterns = [
        # Wash.2d, Wash.3d, Wash.4th, etc.
        r'(\d+)[\s-]*(Wash\.?)[\s-]*(2d|3d|4th|App\.?|\d+)[\s-]*(\d+)',
        # Wash (no series)
        r'(\d+)[\s-]*(Wash\.?)[\s-]*(\d+)',
    ]
    
    # Combine all patterns
    patterns = [re.compile(p, re.IGNORECASE) for p in wn_patterns + wash_patterns]
    
    # Test each pattern against each test case
    for test in test_cases:
        print(f"\nTesting: {test}")
        matched = False
        
        for i, pattern in enumerate(patterns):
            match = pattern.search(test)
            if match:
                matched = True
                print(f"  ✓ Matched pattern {i+1}: {pattern.pattern}")
                print(f"     Groups: {match.groups()}")
                
        if not matched:
            print("  ✗ No match")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_washington_citation_patterns()
        # Pattern 2: Washington Court of Appeals  
        (r'\d+\s+Wn\.\s*App\.\s*\d+[^)]*\(\d{4}\)', "Washington Court of Appeals"),
        # Pattern 3: Pacific Reporter
        (r'\d+\s+P\.\s*\d+\s*\d+[^)]*\(\d{4}\)', "Pacific Reporter"),
        # Pattern 4: General pattern
        (r'\d+\s+[A-Za-z\.]+\s+\d+[^)]*\(\d{4}\)', "General"),
    ]
    
    for pattern, description in patterns:
        print(f"\nTesting {description} pattern: {pattern}")
        matches = list(re.finditer(pattern, toa_section))
        print(f"Found {len(matches)} matches")
        
        for i, match in enumerate(matches[:3]):  # Show first 3
            citation = match.group(0)
            print(f"  {i+1}. {citation}")
            
            # Show context around the citation
            start_pos = max(0, match.start() - 50)
            end_pos = min(len(toa_section), match.end() + 50)
            context = toa_section[start_pos:end_pos]
            print(f"     Context: ...{context}...")

if __name__ == "__main__":
    test_citation_patterns()
