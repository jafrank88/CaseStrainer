#!/usr/bin/env python3
"""
Test script to verify URL field is being passed correctly from backend to frontend.
"""

import sys
import os
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_url_passing():
    """Test that URLs are being passed correctly from backend to frontend."""
    
    from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
    
    # Initialize verifier
    verifier = EnhancedMultiSourceVerifier()
    
    # Test citations that should have URLs
    test_citations = [
        "374 P.3d 63",  # Should be verified with URL
        "185 Wn.2d 363",  # Should be verified with URL
        "410 U.S. 113",   # Roe v. Wade - should be verified with URL
        "347 U.S. 483",   # Brown v. Board - should be verified with URL
    ]
    
    print("🔍 TESTING URL FIELD PASSING")
    print("=" * 60)
    
    for i, citation in enumerate(test_citations, 1):
        print(f"\n📋 Test {i}: {citation}")
        print("-" * 40)
        
        # Test the unified workflow directly
        result = verifier.verify_citation_unified_workflow(citation)
        
        # Analyze the result
        verified = result.get('verified')
        url = result.get('url')
        case_name = result.get('case_name')
        source = result.get('source')
        
        print(f"✅ Verified: {verified}")
        print(f"🔗 URL: {url}")
        print(f"📝 Case Name: {case_name}")
        print(f"🏛️ Source: {source}")
        
        # Check if URL is present and valid
        if url and url.startswith('http'):
            print(f"✅ URL Status: VALID - {url}")
        elif url:
            print(f"⚠️ URL Status: INVALID FORMAT - {url}")
        else:
            print(f"❌ URL Status: MISSING")
            
        # Check frontend compatibility
        if verified in ['true', 'true_by_parallel', True]:
            if url and url.startswith('http'):
                print(f"✅ Frontend Ready: YES - Will show clickable link")
            else:
                print(f"❌ Frontend Ready: NO - Verified but no URL")
        else:
            print(f"ℹ️ Frontend Ready: N/A - Not verified")
            
        # Show complete result for debugging
        print(f"\n📊 Complete Result:")
        print(json.dumps(result, indent=2))
        
    print(f"\n🎯 SUMMARY")
    print("=" * 60)
    
    # Test a simple citation to verify the fix
    print(f"\n🧪 Testing simple citation: 374 P.3d 63")
    result = verifier.verify_citation_unified_workflow("374 P.3d 63")
    
    print(f"Verified: {result.get('verified')}")
    print(f"URL: {result.get('url')}")
    print(f"Case Name: {result.get('case_name')}")
    print(f"Source: {result.get('source')}")
    
    if result.get('verified') == 'true' and result.get('url'):
        print("✅ SUCCESS: URL is being passed correctly!")
    else:
        print("❌ ISSUE: URL is not being passed correctly")

if __name__ == "__main__":
    test_url_passing() 