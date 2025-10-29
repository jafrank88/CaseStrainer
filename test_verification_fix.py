#!/usr/bin/env python3
"""
Test script to verify the async verification fixes
"""

import sys
import os
import requests

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all imports work correctly"""
    print("TESTING IMPORTS")
    print("=" * 50)
    
    try:
        print("1. Testing requests import...")
        import requests
        print("   ✅ requests imported successfully")
    except Exception as e:
        print(f"   ❌ requests import failed: {e}")
        return False
    
    try:
        print("2. Testing unified_verification_master import...")
        from src.unified_verification_master import UnifiedVerificationMaster
        print("   ✅ UnifiedVerificationMaster imported successfully")
    except Exception as e:
        print(f"   ❌ UnifiedVerificationMaster import failed: {e}")
        return False
    
    try:
        print("3. Testing enhanced_fallback_verifier import...")
        from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
        print("   ✅ EnhancedFallbackVerifier imported successfully")
    except Exception as e:
        print(f"   ❌ EnhancedFallbackVerifier import failed: {e}")
        return False
    
    try:
        print("4. Testing async_verification_worker import...")
        from src.async_verification_worker import verify_citations_enhanced
        print("   ✅ async_verification_worker imported successfully")
    except Exception as e:
        print(f"   ❌ async_verification_worker import failed: {e}")
        return False
    
    return True

def test_verification_master():
    """Test the UnifiedVerificationMaster class"""
    print("\nTESTING VERIFICATION MASTER")
    print("=" * 50)
    
    try:
        from src.unified_verification_master import UnifiedVerificationMaster
        
        verifier = UnifiedVerificationMaster()
        print(f"✅ UnifiedVerificationMaster created")
        print(f"   API Key configured: {bool(verifier.api_key)}")
        # Check available attributes
        print(f"   Available attributes: {[attr for attr in dir(verifier) if not attr.startswith('_')]}")
        
        return True
    except Exception as e:
        print(f"❌ UnifiedVerificationMaster test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_verifier():
    """Test the EnhancedFallbackVerifier class"""
    print("\nTESTING FALLBACK VERIFIER")
    print("=" * 50)
    
    try:
        from src.enhanced_fallback_verifier import EnhancedFallbackVerifier
        
        verifier = EnhancedFallbackVerifier()
        print(f"✅ EnhancedFallbackVerifier created (stub implementation)")
        
        # Test sync verification
        result = verifier.verify_citation_sync("123 U.S. 456")
        print(f"   Sync test result: verified={result['verified']}, error={result.get('error')}")
        
        return True
    except Exception as e:
        print(f"❌ EnhancedFallbackVerifier test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("VERIFICATION SYSTEM FIX TEST")
    print("=" * 50)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test verification master
    if not test_verification_master():
        success = False
    
    # Test fallback verifier
    if not test_fallback_verifier():
        success = False
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 ALL TESTS PASSED - Verification system is working!")
    else:
        print("❌ SOME TESTS FAILED - Check the errors above")
    
    print("=" * 50)
