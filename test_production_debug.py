#!/usr/bin/env python3
"""
Debug the production extraction issue step by step
"""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_production_debug():
    """Debug the exact production extraction process"""
    
    # Try to import the extraction function directly
    try:
        from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
        print("✅ Successfully imported unified extraction master")
    except Exception as e:
        print(f"❌ Failed to import: {e}")
        return
    
    # The problematic citation
    citation = "390 U.S. 747, 784 (1968)"
    
    # Test with the exact context that should work
    context = """In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)"""
    
    print("\nPRODUCTION DEBUG TEST")
    print("=" * 60)
    print(f"Citation: {citation}")
    print(f"Context: {context}")
    print()
    
    # Find citation position
    citation_pos = context.find(citation)
    print(f"Citation position: {citation_pos}")
    
    # Test the extraction function
    try:
        result = extract_case_name_and_date_unified_master(
            text=context,
            citation=citation,
            start_index=citation_pos,
            end_index=citation_pos + len(citation),
            debug=True
        )
        
        print(f"\nEXTRACTION RESULT:")
        print(f"  Case name: {result.get('case_name', 'N/A')}")
        print(f"  Date: {result.get('date', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 0):.2f}")
        print(f"  Method: {result.get('method', 'N/A')}")
        
        if result.get('case_name') == 'N/A':
            print("\n❌ PRODUCTION ISSUE CONFIRMED: Getting 'N/A' result")
            
            # Let's check what's happening in the cleaning step
            print("\n🔍 INVESTIGATING THE N/A RESULT:")
            
            # Test the raw extraction step by step
            print("1. Testing comma anchor extraction...")
            
            # Try to call the comma anchor method directly if possible
            try:
                # We need to create an instance to access internal methods
                extractor = extract_case_name_and_date_unified_master.__self__
                if hasattr(extractor, '_extract_with_comma_anchor'):
                    comma_result = extractor._extract_with_comma_anchor(
                        text=context,
                        citation=citation,
                        start_index=citation_pos,
                        debug=True
                    )
                    if comma_result:
                        print(f"   Comma anchor result: {comma_result.case_name}")
                    else:
                        print("   Comma anchor returned None")
                else:
                    print("   Comma anchor method not accessible")
            except Exception as e:
                print(f"   Error testing comma anchor: {e}")
            
    except Exception as e:
        print(f"❌ Extraction failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test if there's a simpler pattern that works
    print("\n🔍 TESTING SIMPLER PATTERNS:")
    
    # Direct regex test
    in_re_pattern = r'In\s+re\s+([A-Z][a-zA-Z0-9\s\'&\-\.,]{3,})'
    match = re.search(in_re_pattern, context)
    if match:
        print(f"✅ Simple regex found: '{match.group(0)}'")
    else:
        print("❌ Simple regex failed")
    
    # Test with the full user text
    print("\n🔍 TESTING WITH FULL USER TEXT:")
    full_text = """County of Hudson v. Dep't of Corr., 703 A.2d 268, 274 (N.J. 1997) ("In general, an agency has the authority to amend, change, or repeal its regulations, especially in response to changing conditions."); Ins. Fed'n of Pa., Inc. v. Commonwealth, Ins. Dep't, 970 A.2d 1108, 1124 (Pa. 2009) ("[A]n agency may revise its policies and amend its regulations in interpreting its statutory mandate." (quoting Elite Indus., Inc. v. Pa. Pub. Util. Comm'n, 832 A.2d 428, 431-32 (Pa. 2003))); Nat'l Ass'n of Mfrs. v. SEC, 105 F.4th 802, 810-11 (5th Cir. 2024) ("An administrative agency may alter or rescind its policies, including when a new administration enters office."); see also Motor Vehicle Mfrs. Ass'n of U.S., Inc. v. State Farm Mut. Auto Ins. Co., 463 U.S. 29, 42 (1983) (noting that agencies "must be given ample latitude to 'adapt their rules and policies to the demands of changing circumstances' " (quoting In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)))"""
    
    citation_pos_full = full_text.find(citation)
    if citation_pos_full != -1:
        print(f"Citation found in full text at position: {citation_pos_full}")
        
        # Get 300 chars before and after
        start = max(0, citation_pos_full - 300)
        end = min(len(full_text), citation_pos_full + len(citation) + 300)
        context_full = full_text[start:end]
        
        print(f"Context length: {len(context_full)}")
        print(f"Context: {context_full}")
        
        # Test extraction with full context
        try:
            result_full = extract_case_name_and_date_unified_master(
                text=context_full,
                citation=citation,
                start_index=citation_pos_full - start,
                end_index=citation_pos_full - start + len(citation),
                debug=False  # Reduce noise
            )
            
            print(f"\nFULL TEXT EXTRACTION RESULT:")
            print(f"  Case name: {result_full.get('case_name', 'N/A')}")
            print(f"  Date: {result_full.get('date', 'N/A')}")
            print(f"  Confidence: {result_full.get('confidence', 0):.2f}")
            
        except Exception as e:
            print(f"❌ Full text extraction failed: {e}")

if __name__ == "__main__":
    test_production_debug()
