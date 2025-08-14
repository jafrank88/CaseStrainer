#!/usr/bin/env python3
"""
Simple eyecite test to verify it's working correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_eyecite_directly():
    """Test eyecite directly without our wrapper"""
    print("=" * 60)
    print("TESTING EYECITE DIRECTLY")
    print("=" * 60)
    
    try:
        # Test eyecite import
        print("1. Testing eyecite import...")
        import eyecite
        from eyecite import get_citations
        from eyecite.tokenizers import AhocorasickTokenizer
        print("✓ Eyecite imported successfully")
        
        # Test basic extraction
        test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
        print(f"\n2. Testing extraction on: {test_text}")
        
        tokenizer = AhocorasickTokenizer()
        citations = get_citations(test_text, tokenizer=tokenizer)
        
        print(f"✓ Found {len(citations)} citations")
        
        for i, citation in enumerate(citations):
            print(f"\nCitation {i+1}:")
            print(f"  Type: {type(citation)}")
            print(f"  String: {str(citation)}")
            print(f"  Has groups: {hasattr(citation, 'groups')}")
            
            if hasattr(citation, 'groups'):
                print(f"  Groups type: {type(citation.groups)}")
                print(f"  Groups: {citation.groups}")
                
            if hasattr(citation, 'metadata'):
                print(f"  Has metadata: True")
                print(f"  Metadata: {citation.metadata}")
            else:
                print(f"  Has metadata: False")
        
        return len(citations) > 0
        
    except Exception as e:
        print(f"✗ Eyecite test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_regex_extraction():
    """Test basic regex extraction patterns"""
    print("\n" + "=" * 60)
    print("TESTING BASIC REGEX PATTERNS")
    print("=" * 60)
    
    import re
    
    test_text = "Brown v. Board of Education, 347 U.S. 483 (1954)"
    
    # Basic citation patterns
    patterns = [
        r'\b\d+\s+U\.S\.\s+\d+\b',
        r'\b\d+\s+[A-Za-z.]+\s+\d+\b',
        r'\b\d+\s+[A-Za-z.]+(?:\s+[A-Za-z.]+)?\s+\d+\b'
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\nPattern {i}: {pattern}")
        matches = re.findall(pattern, test_text)
        print(f"  Matches: {matches}")
    
    return len(matches) > 0

def main():
    """Run simple tests"""
    print("SIMPLE EYECITE AND REGEX TEST")
    
    eyecite_works = test_eyecite_directly()
    regex_works = test_regex_extraction()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Eyecite Direct: {'✓ PASS' if eyecite_works else '✗ FAIL'}")
    print(f"Regex Patterns: {'✓ PASS' if regex_works else '✗ FAIL'}")

if __name__ == "__main__":
    main()
