#!/usr/bin/env python3
"""
Test script to check canonical service functionality.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_canonical_service():
    """Test the canonical service directly."""
    try:
        from canonical_case_name_service import get_canonical_case_name_with_date
        
        print("Testing canonical service...")
        
        # Test with the fake citation
        result = get_canonical_case_name_with_date("999 U.S. 999")
        print(f"Result for '999 U.S. 999': {result}")
        
        # Test with a known fallback citation
        result2 = get_canonical_case_name_with_date("410 U.S. 113")
        print(f"Result for '410 U.S. 113': {result2}")
        
        return True
        
    except Exception as e:
        print(f"Error testing canonical service: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_canonical_service()
    if success:
        print("✅ Canonical service test passed")
    else:
        print("❌ Canonical service test failed") 