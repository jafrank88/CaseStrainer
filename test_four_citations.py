#!/usr/bin/env python3
"""
Test script to run the four specific citations through multi-search verification.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
import json

def test_citation_verification():
    """Test the four specific citations through multi-search."""
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # The four citations to test
    citations = [
        "219 L.Ed. 2d 420",
        "144 S.Ct. 1785", 
        "515 P.3d 1029",
        "129 S.Ct. 2529"
    ]
    
    print("=" * 80)
    print("MULTI-SEARCH VERIFICATION TEST")
    print("=" * 80)
    
    for i, citation in enumerate(citations, 1):
        print(f"\n{i}. Testing citation: {citation}")
        print("-" * 60)
        
        # Test each source individually
        print("Testing individual sources:")
        
        # 1. CourtListener
        print("\n  CourtListener:")
        try:
            courtlistener_result = verifier._try_courtlistener(citation)
            print(f"    Verified: {courtlistener_result.get('verified', False)}")
            print(f"    Source: {courtlistener_result.get('source', 'N/A')}")
            if courtlistener_result.get('error'):
                print(f"    Error: {courtlistener_result.get('error')}")
            if courtlistener_result.get('case_name'):
                print(f"    Case: {courtlistener_result.get('case_name')}")
        except Exception as e:
            print(f"    Error: {str(e)}")
        
        # 2. Google Scholar
        print("\n  Google Scholar:")
        try:
            google_result = verifier._try_google_scholar(citation)
            print(f"    Verified: {google_result.get('verified', False)}")
            print(f"    Source: {google_result.get('source', 'N/A')}")
            if google_result.get('error'):
                print(f"    Error: {google_result.get('error')}")
            if google_result.get('case_name'):
                print(f"    Case: {google_result.get('case_name')}")
        except Exception as e:
            print(f"    Error: {str(e)}")
        
        # 3. Justia
        print("\n  Justia:")
        try:
            justia_result = verifier._try_justia(citation)
            print(f"    Verified: {justia_result.get('verified', False)}")
            print(f"    Source: {justia_result.get('source', 'N/A')}")
            if justia_result.get('error'):
                print(f"    Error: {justia_result.get('error')}")
            if justia_result.get('case_name'):
                print(f"    Case: {justia_result.get('case_name')}")
        except Exception as e:
            print(f"    Error: {str(e)}")
        
        # 4. Leagle
        print("\n  Leagle:")
        try:
            leagle_result = verifier._try_leagle(citation)
            print(f"    Verified: {leagle_result.get('verified', False)}")
            print(f"    Source: {leagle_result.get('source', 'N/A')}")
            if leagle_result.get('error'):
                print(f"    Error: {leagle_result.get('error')}")
            if leagle_result.get('case_name'):
                print(f"    Case: {leagle_result.get('case_name')}")
        except Exception as e:
            print(f"    Error: {str(e)}")
        
        # 5. FindLaw
        print("\n  FindLaw:")
        try:
            findlaw_result = verifier._try_findlaw(citation)
            print(f"    Verified: {findlaw_result.get('verified', False)}")
            print(f"    Source: {findlaw_result.get('source', 'N/A')}")
            if findlaw_result.get('error'):
                print(f"    Error: {findlaw_result.get('error')}")
            if findlaw_result.get('case_name'):
                print(f"    Case: {findlaw_result.get('case_name')}")
        except Exception as e:
            print(f"    Error: {str(e)}")
        
        # 6. CaseText
        print("\n  CaseText:")
        try:
            casetext_result = verifier._try_casetext(citation)
            print(f"    Verified: {casetext_result.get('verified', False)}")
            print(f"    Source: {casetext_result.get('source', 'N/A')}")
            if casetext_result.get('error'):
                print(f"    Error: {casetext_result.get('error')}")
            if casetext_result.get('case_name'):
                print(f"    Case: {casetext_result.get('case_name')}")
        except Exception as e:
            print(f"    Error: {str(e)}")
        
        # Now test the full multi-search process
        print(f"\n  Full Multi-Search Result:")
        try:
            full_result = verifier.verify_citation(citation, use_cache=False, use_api=True, force_refresh=True)
            print(f"    Final Verified: {full_result.get('verified', False)}")
            print(f"    Final Source: {full_result.get('source', 'N/A')}")
            print(f"    Final Error: {full_result.get('error', 'None')}")
            if full_result.get('verification_steps'):
                print(f"    Steps: {len(full_result.get('verification_steps', []))} steps completed")
        except Exception as e:
            print(f"    Error in full verification: {str(e)}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    test_citation_verification() 