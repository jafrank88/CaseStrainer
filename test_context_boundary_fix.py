#!/usr/bin/env python3
"""
Test script to verify the context boundary detection fix works correctly
for the problematic "City of Bellevue v. Lorang" bleeding issue.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_context_boundary_fix():
    """Test the fixed context boundary detection"""
    
    print("🔍 TESTING CONTEXT BOUNDARY DETECTION FIX")
    print("=" * 50)
    
    # Test the problematic citation cluster from the PDF
    test_text = """Young v. Pierce County , 120 Wn. App. 175, 188, 84 P.3d 927 (2004)  (alteration in original)   (quoting City of Bellevue v. Lorang , 140 Wn.2d 19, 32, 992 P.2d 496 (2000) ).   Petitioners appear to contend that the alleged errors were not harmless because "[had]  Jefferson County allowed its code interpretation to be placed before the hearing examiner, the various issues before this Court, minimum lot size and zoning density 's relationship to a  'buildable lot' could have been resolved."""
    
    try:
        from src.utils.strict_context_isolator import (
            find_all_citation_positions,
            get_strict_context_for_citation,
            extract_case_name_from_strict_context
        )
        
        # Find all citation positions
        citations = find_all_citation_positions(test_text)
        
        print(f"📋 Found {len(citations)} citations:")
        for i, (start, end, cit_text) in enumerate(citations, 1):
            print(f"  {i}. {cit_text} at {start}-{end}")
        
        # Test context isolation for each problematic citation
        problematic_citations = [
            "120 Wn. App. 175",
            "84 P.3d 927", 
            "140 Wn.2d 19",
            "992 P.2d 496"
        ]
        
        print(f"\n🎯 TESTING CONTEXT ISOLATION:")
        
        for cit_text in problematic_citations:
            # Find the citation position
            cit_pos = None
            for start, end, text in citations:
                if cit_text in text:
                    cit_pos = (start, end)
                    break
            
            if not cit_pos:
                print(f"❌ {cit_text}: Position not found")
                continue
                
            start, end = cit_pos
            
            # Get strict context
            strict_context = get_strict_context_for_citation(
                test_text, start, end, citations, max_lookback=300
            )
            
            # Extract case name
            case_name = extract_case_name_from_strict_context(strict_context, cit_text)
            
            print(f"\n🔍 {cit_text}:")
            print(f"   Position: {start}-{end}")
            print(f"   Context: '{strict_context}'")
            print(f"   Extracted: '{case_name if case_name else 'None'}'")
            
            # Verify expectations
            if cit_text in ["120 Wn. App. 175", "84 P.3d 927"]:
                expected = "Young v. Pierce County"
                if case_name and expected in case_name:
                    print(f"   ✅ CORRECT: Got expected case name")
                else:
                    print(f"   ❌ ERROR: Expected '{expected}', got '{case_name}'")
                    
            elif cit_text in ["140 Wn.2d 19", "992 P.2d 496"]:
                expected = "City of Bellevue v. Lorang"
                if case_name and expected in case_name:
                    print(f"   ✅ CORRECT: Got expected case name")
                else:
                    print(f"   ❌ ERROR: Expected '{expected}', got '{case_name}'")
        
        print(f"\n📊 SUMMARY:")
        print(f"This test verifies that the context boundary detection prevents")
        print(f"'City of Bellevue v. Lorang' from bleeding into other citations.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_boundary_fix()
