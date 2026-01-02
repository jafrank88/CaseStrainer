#!/usr/bin/env python3
"""
Test the context boundary fix with other state reporters to verify 
the parallel citation detection works broadly, not just for Washington.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.strict_context_isolator import (
    get_strict_context_for_citation,
    extract_case_name_from_strict_context
)

def test_other_state_reporters():
    """Test parallel citation clusters with various state reporters"""
    
    print("🔍 TESTING CONTEXT BOUNDARY FIX WITH OTHER STATE REPORTERS")
    print("=" * 70)
    
    # Test cases with different state reporters in parallel citation clusters
    test_cases = [
        {
            "text": "Smith v. Jones , 123 Cal. 456, 789, 456 P.2d 123 (2003)",
            "citations": ["123 Cal. 456", "456 P.2d 123"],
            "expected": "Smith v. Jones"
        },
        {
            "text": "Brown v. Board , 234 N.Y. 567, 890, 345 N.E.2d 234 (2004)",
            "citations": ["234 N.Y. 567", "345 N.E.2d 234"], 
            "expected": "Brown v. Board"
        },
        {
            "text": "Johnson v. Smith , 345 Ill. App. 678, 901, 567 N.E.3d 345 (2005)",
            "citations": ["345 Ill. App. 678", "567 N.E.3d 345"],
            "expected": "Johnson v. Smith"
        },
        {
            "text": "Davis v. Miller , 456 Ga. 123, 456, 678 S.E.2d 456 (2006)",
            "citations": ["456 Ga. 123", "678 S.E.2d 456"],
            "expected": "Davis v. Miller"
        },
        {
            "text": "Wilson v. Taylor , 567 Tex. 234, 567, 789 S.W.3d 567 (2007)",
            "citations": ["567 Tex. 234", "789 S.W.3d 567"],
            "expected": "Wilson v. Taylor"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['expected']}")
        print(f"Text: {test_case['text']}")
        
        # Find citation positions (simplified)
        all_citations = []
        for citation in test_case["citations"]:
            start = test_case["text"].find(citation)
            if start != -1:
                end = start + len(citation)
                all_citations.append((start, end, citation))
        
        all_citations.sort()  # Sort by position
        
        print(f"📋 Found {len(all_citations)} citations:")
        for j, (start, end, cit_text) in enumerate(all_citations, 1):
            print(f"  {j}. {cit_text} at {start}-{end}")
            
            # Get context and extract case name
            try:
                context = get_strict_context_for_citation(
                    test_case["text"], start, end, all_citations
                )
                extracted = extract_case_name_from_strict_context(
                    context, cit_text
                )
                
                print(f"   Context: '{context}'")
                print(f"   Extracted: '{extracted}'")
                
                if extracted == test_case["expected"]:
                    print(f"   ✅ CORRECT: Got expected case name")
                else:
                    print(f"   ❌ ERROR: Expected '{test_case['expected']}', got '{extracted}'")
                    
            except Exception as e:
                print(f"   ❌ EXCEPTION: {e}")
        
        print("-" * 50)
    
    print("\n📊 SUMMARY:")
    print("This test verifies that the parallel citation detection")
    print("works for multiple state reporters, not just Washington.")

if __name__ == "__main__":
    test_other_state_reporters()
