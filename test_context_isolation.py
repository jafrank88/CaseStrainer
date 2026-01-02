#!/usr/bin/env python3
"""
Test script to verify context isolation for the specific case mentioned by user
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.clean_extraction_pipeline import extract_citations_clean

def test_context_isolation():
    """Test that context isolation properly associates case names with citations"""
    
    # The exact text from the user's document
    test_text = '''A petitioner can recover relief for improper process under LUPA "unless the error was harmless." RCW 36.70C.130(1)(a). A harmless error is one that is "'not prejudicial to the substantial rights of the party assigning [error,]' and does not affect the outcome of the case." Young v. Pierce County, 120 Wn. App. 175, 188, 84 P.3d 927 (2004) (alteration in original) (quoting City of Bellevue v. Lorang, 140 Wn.2d 19, 32, 992 P.2d 496 (2000))'''
    
    print("🧪 TESTING CONTEXT ISOLATION")
    print("=" * 60)
    print("Text:", test_text)
    print()
    
    # Extract citations using the clean pipeline
    citations = extract_citations_clean(test_text)
    
    print(f"📊 Found {len(citations)} citations:")
    print()
    
    for i, citation in enumerate(citations):
        print(f"Citation {i + 1}: {citation.citation}")
        print(f"  Extracted Case Name: {citation.extracted_case_name}")
        print(f"  Extracted Date: {citation.extracted_date}")
        print(f"  Start Index: {citation.start_index}")
        print(f"  End Index: {citation.end_index}")
        print()
        
        # Check if this is the Lorang citation
        if "140 Wn.2d 19" in citation.citation or "992 P.2d 496" in citation.citation:
            print("  🎯 FOUND LORANG CITATION!")
            if citation.extracted_case_name == "City of Bellevue v. Lorang":
                print("  ✅ CORRECT: Properly associated with 'City of Bellevue v. Lorang'")
            else:
                print(f"  ❌ ERROR: Should be 'City of Bellevue v. Lorang' but got '{citation.extracted_case_name}'")
        
        # Check if this is a different citation that incorrectly got Lorang's name
        elif citation.extracted_case_name == "City of Bellevue v. Lorang":
            print(f"  🚨 CONTAMINATION: Wrong citation '{citation.citation}' got Lorang's case name!")
    
    print("=" * 60)
    print("📋 ANALYSIS:")
    print("Expected behavior:")
    print("- Only citations 140 Wn.2d 19 and 992 P.2d 496 should have 'City of Bellevue v. Lorang'")
    print("- Other citations (120 Wn. App. 175, 84 P.3d 927) should have 'Young v. Pierce County'")
    print()
    print("If other citations have Lorang's name, context isolation is failing.")

if __name__ == "__main__":
    test_context_isolation()
