#!/usr/bin/env python3
"""
Test script to directly test the _process_courtlistener_result method.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_process_courtlistener_result():
    """Test the _process_courtlistener_result method directly."""
    
    # Create verifier instance
    verifier = EnhancedMultiSourceVerifier()
    
    # Sample CourtListener response (from the logs)
    sample_response = {
        "resource_uri": "https://www.courtlistener.com/api/rest/v4/clusters/105221/",
        "id": 105221,
        "absolute_url": "/opinion/105221/brown-v-board-of-education/",
        "panel": [],
        "non_participating_judges": [],
        "docket_id": 84657,
        "docket": "https://www.courtlistener.com/api/rest/v4/dockets/84657/",
        "sub_opinions": [
            "https://www.courtlistener.com/api/rest/v4/opinions/105221/"
        ],
        "citations": [
            {
                "volume": 98,
                "reporter": "L. Ed. 2d",
                "page": "873",
                "type": 1
            },
            {
                "volume": 74,
                "reporter": "S. Ct.",
                "page": "483",
                "type": 1
            }
        ]
    }
    
    print("Testing _process_courtlistener_result method:")
    print("=" * 60)
    print(f"Input citation: 347 U.S. 483")
    print(f"Input response: {sample_response}")
    print("=" * 60)
    
    try:
        # Call the method directly
        result = verifier._process_courtlistener_result("347 U.S. 483", sample_response)
        
        print(f"\nResult:")
        print(f"  Verified: {result.get('verified')}")
        print(f"  Case Name: {result.get('case_name')}")
        print(f"  Canonical Name: {result.get('canonical_name')}")
        print(f"  URL: {result.get('url')}")
        print(f"  Source: {result.get('source')}")
        
        # Check if canonical name was extracted
        canonical_name = result.get('canonical_name', '')
        if canonical_name and canonical_name != '':
            print(f"  ✓ SUCCESS: Canonical name extracted: '{canonical_name}'")
        else:
            print(f"  ✗ FAILED: No canonical name extracted")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_process_courtlistener_result() 