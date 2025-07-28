#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify that the 500 Internal Server Error is fixed.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_function_signature_fix():
    """Test that the verify_with_courtlistener function signature is fixed."""
    
    print("Testing 500 Internal Server Error Fix")
    print("=" * 50)
    
    try:
        # Test importing both versions of the function
        from citation_verification import verify_with_courtlistener as verify_old
        from courtlistener_verification import verify_with_courtlistener as verify_new
        
        print("✅ Both function imports successful")
        
        # Test function signatures
        import inspect
        
        # Check old function signature
        old_sig = inspect.signature(verify_old)
        print(f"Old function signature: verify_with_courtlistener{old_sig}")
        
        # Check new function signature  
        new_sig = inspect.signature(verify_new)
        print(f"New function signature: verify_with_courtlistener{new_sig}")
        
        # Verify they have the same parameters
        old_params = list(old_sig.parameters.keys())
        new_params = list(new_sig.parameters.keys())
        
        if old_params == new_params:
            print("✅ Function signatures match!")
            print(f"   Parameters: {old_params}")
        else:
            print("❌ Function signatures don't match")
            print(f"   Old: {old_params}")
            print(f"   New: {new_params}")
            return False
        
        # Test that both functions can be called with the same arguments
        print("\nTesting function calls with same arguments:")
        
        # Mock API key for testing
        api_key = "test_key"
        citation = "123 U.S. 456"
        extracted_case_name = "Test v. Case"
        
        try:
            # This should not raise an exception anymore
            print("Testing old function call with 3 arguments...")
            # We won't actually call it since we don't have a real API key
            # Just verify the signature accepts the call
            old_sig.bind(api_key, citation, extracted_case_name)
            print("✅ Old function accepts 3 arguments")
            
            print("Testing new function call with 3 arguments...")
            new_sig.bind(api_key, citation, extracted_case_name)
            print("✅ New function accepts 3 arguments")
            
        except TypeError as e:
            print(f"❌ Function call failed: {e}")
            return False
        
        print("\n🎉 500 Internal Server Error should be FIXED!")
        print("The verify_with_courtlistener function signatures now match.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == '__main__':
    success = test_function_signature_fix()
    if success:
        print("\n✅ All tests passed! The 500 error should be resolved.")
    else:
        print("\n❌ Tests failed. The 500 error may still occur.")
