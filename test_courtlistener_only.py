#!/usr/bin/env python3
"""
Simple test to isolate the CourtListener error.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

def test_courtlistener_only():
    """Test only the CourtListener method to isolate the error."""
    
    verifier = EnhancedMultiSourceVerifier()
    citation = "219 L.Ed. 2d 420"
    
    print(f"Testing CourtListener with citation: {citation}")
    print("=" * 50)
    
    try:
        # Test the _try_courtlistener method directly
        print("Testing _try_courtlistener method:")
        result = verifier._try_courtlistener(citation)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error in _try_courtlistener: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    
    try:
        # Test the _verify_with_courtlistener method directly
        print("Testing _verify_with_courtlistener method:")
        result = verifier._verify_with_courtlistener(citation)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error in _verify_with_courtlistener: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_courtlistener_only() 