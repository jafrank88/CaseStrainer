#!/usr/bin/env python3
"""
Test script to see what eyecite extracts from the test text.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    import eyecite
    from eyecite import get_citations
    print("Eyecite available")
    
    # The test text
    test_text = """We review a trial court's findings of fact for substantial evidence, generally 
deferring to the trier of fact on questions of witness credibility, conflicting 
testimony, and persuasiveness of the evidence. In re Vulnerable Adult Petition 
for Knight, 178 Wn. App. 929, 936-37, 317 P.3d 1068 (2014). Evidence is 
substantial when sufficient to persuade a fair-minded person of the truth of the 
matter asserted. In re Marriage of Black, 188 Wn.2d 114, 127, 392 P.3d 1041 
(2017). "Competent evidence sufficient to support the trial court's decision to 
grant . . . a domestic violence protection order may contain hearsay or be wholly 
documentary." Blackmon v. Blackmon, 155 Wn. App. 715, 722, 230 P.3d 233 
(2010)."""
    
    print("=== Testing Eyecite Extraction ===")
    print(f"Test text length: {len(test_text)} characters")
    print()
    
    # Extract citations with eyecite
    citations = get_citations(test_text)
    
    print(f"Eyecite found {len(citations)} citations:")
    for i, citation in enumerate(citations):
        print(f"Citation {i+1}: {citation}")
        print(f"  Type: {type(citation).__name__}")
        if hasattr(citation, 'citation'):
            print(f"  Citation: {citation.citation}")
        if hasattr(citation, 'groups'):
            print(f"  Groups: {citation.groups}")
        print()
    
except ImportError:
    print("Eyecite not available")
except Exception as e:
    print(f"Error: {e}")
