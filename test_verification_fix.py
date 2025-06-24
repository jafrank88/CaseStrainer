#!/usr/bin/env python3
"""
Test script to verify the new stricter citation verification logic.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_verification_logic():
    """Test the new verification logic with problematic citations."""
    
    print("Testing new citation verification logic...")
    print("=" * 60)
    
    # Initialize the verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Clear cache to ensure fresh verification
    verifier.clear_cache()
    
    # Test cases that were previously incorrectly marked as verified
    test_citations = [
        "181 Wash.2d 391",
        "334 P.3d 519",
        "123 F.3d 456",  # Example citation
        "456 U.S. 789",  # Example citation
    ]
    
    for citation in test_citations:
        print(f"\nTesting citation: {citation}")
        print("-" * 40)
        
        try:
            # Test with force_refresh to bypass cache
            result = verifier.verify_citation(
                citation, 
                extracted_case_name="s prior decision in Walston v. Boeing Co",
                force_refresh=True
            )
            
            print(f"Verified: {result.get('verified', False)}")
            print(f"Sources: {result.get('sources', [])}")
            print(f"Case name: {result.get('case_name', 'N/A')}")
            print(f"Verification reason: {result.get('verification_reason', 'N/A')}")
            print(f"CourtListener verified: {result.get('courtlistener_verified', False)}")
            
            # Show individual results
            if 'results' in result:
                print("\nIndividual source results:")
                for source_name, source_result in result['results']:
                    verified = source_result.get('verified', False)
                    case_name = source_result.get('case_name', 'N/A')
                    error = source_result.get('error', 'N/A')
                    print(f"  {source_name}: verified={verified}, case_name='{case_name}', error='{error}'")
            
        except Exception as e:
            print(f"Error testing citation {citation}: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed.")

if __name__ == "__main__":
    test_verification_logic() 