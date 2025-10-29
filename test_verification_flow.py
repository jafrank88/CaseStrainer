#!/usr/bin/env python3
"""
Test the verification flow that might be corrupting the case name
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_verification_flow():
    """Test if verification is corrupting the case name"""
    
    print("VERIFICATION FLOW TEST")
    print("=" * 60)
    
    # Test the CourtListener verification directly
    try:
        from src.courtlistener_verification import verify_with_courtlistener
        
        citation = "390 U.S. 747"
        extracted_name = "In re Permian Basin Area Rate Cases"
        
        print(f"Testing CourtListener verification for:")
        print(f"  Citation: {citation}")
        print(f"  Extracted name: {extracted_name}")
        print()
        
        # Test verification
        result = verify_with_courtlistener(citation, extracted_name)
        
        print("VERIFICATION RESULT:")
        print(f"  Case name: {result.get('case_name', 'N/A')}")
        print(f"  Canonical name: {result.get('canonical_name', 'N/A')}")
        print(f"  Canonical date: {result.get('canonical_date', 'N/A')}")
        print(f"  URL: {result.get('url', 'N/A')}")
        print(f"  Status: {result.get('status', 'N/A')}")
        print(f"  Verified: {result.get('verified', False)}")
        
        if result.get('canonical_name') == 'N/A' or not result.get('canonical_name'):
            print("\n⚠️  WARNING: CourtListener returned no canonical name")
            print("This might be causing the extraction to be corrupted")
        
    except Exception as e:
        print(f"❌ CourtListener verification failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test if there's an issue with the citation format
    print("\n" + "=" * 60)
    print("TESTING DIFFERENT CITATION FORMATS:")
    
    test_citations = [
        "390 U.S. 747",
        "390 U.S. 747, 784", 
        "390 US 747",
        "390 U.S. 747, 784 (1968)"
    ]
    
    for test_citation in test_citations:
        print(f"\nTesting: {test_citation}")
        try:
            result = verify_with_courtlistener(test_citation, "In re Permian Basin Area Rate Cases")
            canonical = result.get('canonical_name', 'N/A')
            status = result.get('status', 'N/A')
            print(f"  Canonical: {canonical}")
            print(f"  Status: {status}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    test_verification_flow()
