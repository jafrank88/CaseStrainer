#!/usr/bin/env python3

def debug_citation_string():
    """Find the exact citation string in the test text."""
    
    # Test text with both citations
    test_text = """
    Municipal corporations are not typically within the zone of interest of individual constitutional guarantees. 
    See, e.g., Lakehaven Water & Sewer Dist. v. City of Fed. Way, 195 Wn.2d 742, 773, 466 P.3d 213 (2020) 
    (sewer and water district lacked standing to challenge constitutional issues).
    
    The State has a duty to actively provide criminal defense services to those who cannot afford it. 
    See Davison v. State, 196 Wn.2d 285, 293, 466 P.3d 231 (2020) 
    ("The State plainly has a duty to provide indigent defense").
    """
    
    print("=== CITATION STRING DEBUG ===")
    print(f"Test text: {repr(test_text)}")
    print()
    
    # Try different variations of the citation string
    citation_variations = [
        "196 Wn. 2d 285",
        "196 Wn.2d 285",
        "196 Wn. 2d 285,",
        "196 Wn.2d 285,",
        "196 Wn. 2d 285, 293",
        "196 Wn.2d 285, 293"
    ]
    
    for citation in citation_variations:
        pos = test_text.find(citation)
        if pos != -1:
            print(f"✅ Found '{citation}' at position {pos}")
        else:
            print(f"❌ Not found: '{citation}'")
    
    print()
    
    # Look for any pattern that matches
    import re
    patterns = [
        r"196\s+Wn\.?\s*2d\s+285",
        r"196\s+Wn\.?\s*2d\s+285,?\s*\d*",
        r"\d+\s+Wn\.?\s*2d\s+\d+"
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, test_text)
        for match in matches:
            print(f"✅ Pattern '{pattern}' found: '{match.group(0)}' at position {match.start()}")

if __name__ == "__main__":
    debug_citation_string() 