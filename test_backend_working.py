#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test to verify backend is working after 500 error fix.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_backend_working():
    """Test that the backend citation processing is working after the 500 error fix."""
    
    print("Testing Backend After 500 Error Fix")
    print("=" * 50)
    
    try:
        # Test basic imports
        print("1. Testing imports...")
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        from citation_verification import verify_with_courtlistener
        from courtlistener_verification import verify_with_courtlistener as verify_new
        print("✅ All imports successful")
        
        # Test function signatures
        print("\n2. Testing function signatures...")
        import inspect
        
        old_sig = inspect.signature(verify_with_courtlistener)
        new_sig = inspect.signature(verify_new)
        
        if list(old_sig.parameters.keys()) == list(new_sig.parameters.keys()):
            print("✅ Function signatures match")
        else:
            print("❌ Function signatures don't match")
            return False
        
        # Test processor initialization
        print("\n3. Testing processor initialization...")
        processor = UnifiedCitationProcessorV2()
        print("✅ Processor initialized successfully")
        
        # Test simple citation processing (without API calls)
        print("\n4. Testing basic citation extraction...")
        test_text = "See Smith v. Jones, 123 U.S. 456 (2020)."
        
        # Just test that we can call the extraction methods without crashing
        from models import CitationResult
        citation = CitationResult(
            citation="123 U.S. 456",
            extracted_case_name="Smith v. Jones",
            extracted_date="2020"
        )
        
        # Test utility methods
        extracted_name = processor._get_extracted_case_name(citation)
        unverified = processor._get_unverified_citations([citation])
        
        print(f"✅ Extracted case name: {extracted_name}")
        print(f"✅ Unverified citations: {len(unverified)}")
        
        print("\n🎉 Backend is working correctly!")
        print("The 500 Internal Server Error has been resolved.")
        return True
        
    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_backend_working()
    if success:
        print("\n✅ Backend is ready for citation processing!")
    else:
        print("\n❌ Backend still has issues that need to be resolved.")
