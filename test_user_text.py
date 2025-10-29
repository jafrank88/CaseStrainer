#!/usr/bin/env python3
"""
Test the exact user text that failed extraction
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_user_text():
    """Test extraction with the exact user text"""
    
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
    
    # The exact user text
    user_text = """County of Hudson v. Dep't of Corr., 703 A.2d 268, 274 (N.J. 1997) ("In general, an agency has the authority to amend, change, or repeal its regulations, especially in response to changing conditions."); Ins. Fed'n of Pa., Inc. v. Commonwealth, Ins. Dep't, 970 A.2d 1108, 1124 (Pa. 2009) ("[A]n agency may revise its policies and amend its regulations in interpreting its statutory mandate." (quoting Elite Indus., Inc. v. Pa. Pub. Util. Comm'n, 832 A.2d 428, 431-32 (Pa. 2003))); Nat'l Ass'n of Mfrs. v. SEC, 105 F.4th 802, 810-11 (5th Cir. 2024) ("An administrative agency may alter or rescind its policies, including when a new administration enters office."); see also Motor Vehicle Mfrs. Ass'n of U.S., Inc. v. State Farm Mut. Auto Ins. Co., 463 U.S. 29, 42 (1983) (noting that agencies "must be given ample latitude to 'adapt their rules and policies to the demands of changing circumstances' " (quoting In re Permian Basin Area Rate Cases, 390 U.S. 747, 784 (1968)))"""
    
    print("USER TEXT EXTRACTION TEST")
    print("=" * 80)
    print("Text length:", len(user_text))
    print()
    
    # Process the text
    processor = UnifiedCitationProcessorV2()
    result = processor.process_text(user_text)
    
    print("PROCESSING RESULTS:")
    print(f"  Total citations found: {len(result.get('citations', []))}")
    print()
    
    # Look for the Permian Basin citation
    citations = result.get('citations', [])
    permian_citation = None
    
    for i, citation in enumerate(citations):
        print(f"Citation {i+1}: {citation.get('citation', 'N/A')}")
        print(f"  Case name: {citation.get('case_name', 'N/A')}")
        print(f"  Extracted date: {citation.get('extracted_date', 'N/A')}")
        print(f"  Verified: {citation.get('verified', False)}")
        
        if '390 U.S. 747' in citation.get('citation', ''):
            permian_citation = citation
            print("  🎯 FOUND PERMIAN BASIN CITATION")
        print()
    
    if permian_citation:
        print("PERMIAN BASIN CITATION DETAILS:")
        print(f"  Citation: {permian_citation.get('citation', 'N/A')}")
        print(f"  Case name: {permian_citation.get('case_name', 'N/A')}")
        print(f"  Extracted date: {permian_citation.get('extracted_date', 'N/A')}")
        print(f"  Canonical name: {permian_citation.get('canonical_name', 'N/A')}")
        print(f"  Canonical date: {permian_citation.get('canonical_date', 'N/A')}")
        print(f"  Verification status: {permian_citation.get('verification_status', 'N/A')}")
        print(f"  Verified: {permian_citation.get('verified', False)}")
        
        if permian_citation.get('case_name') == 'N/A':
            print("\n❌ ISSUE CONFIRMED: Permian Basin citation shows 'N/A' as case name")
            
            # Let's debug this specific citation
            print("\n🔍 DEBUGGING THE FAILED CITATION:")
            citation_text = permian_citation.get('citation', '')
            
            # Find it in the original text
            citation_pos = user_text.find(citation_text)
            if citation_pos != -1:
                print(f"Citation found at position: {citation_pos}")
                
                # Get context around it
                start = max(0, citation_pos - 200)
                end = min(len(user_text), citation_pos + len(citation_text) + 200)
                context = user_text[start:end]
                
                print(f"Context: {context}")
                print()
                
                # Test extraction directly
                from src.unified_case_extraction_master import extract_case_name_and_date_unified_master
                
                debug_result = extract_case_name_and_date_unified_master(
                    text=context,
                    citation=citation_text,
                    start_index=citation_pos - start,
                    end_index=citation_pos - start + len(citation_text),
                    debug=True
                )
                
                print(f"Direct extraction result: {debug_result.get('case_name', 'N/A')}")
    else:
        print("❌ Permian Basin citation not found in results")

if __name__ == "__main__":
    test_user_text()
