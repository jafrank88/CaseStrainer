#!/usr/bin/env python3
"""
Direct test of the verification master to isolate the issue
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_verification_master import get_master_verifier
import asyncio

async def test_verification_direct():
    """Test verification master directly"""
    
    print("🔍 TESTING VERIFICATION MASTER DIRECTLY")
    print("=" * 50)
    
    try:
        verifier = get_master_verifier()
        print(f"✅ Verifier initialized: {type(verifier).__name__}")
        print(f"🔑 API Key present: {'Yes' if verifier.api_key else 'No'}")
        
        # Test with a well-known citation
        citation_text = "347 U.S. 483"
        case_name = "Brown v. Board of Education"
        case_date = "1954"
        
        print(f"\n📋 Testing citation: {citation_text}")
        print(f"   Case name: {case_name}")
        print(f"   Date: {case_date}")
        
        # Test batch verification
        print("\n🔄 Running batch verification...")
        result = await verifier.verify_citations_batch(
            [citation_text], 
            [case_name], 
            [case_date]
        )
        
        print(f"📊 Verification result: {type(result)}")
        if result and len(result) > 0:
            verified_citation = result[0]
            print(f"   Verified: {getattr(verified_citation, 'verified', 'N/A')}")
            print(f"   Canonical name: {getattr(verified_citation, 'canonical_name', 'N/A')}")
            print(f"   Canonical URL: {getattr(verified_citation, 'canonical_url', 'N/A')}")
            print(f"   Source: {getattr(verified_citation, 'source', 'N/A')}")
            print(f"   Error: {getattr(verified_citation, 'error', 'N/A')}")
        else:
            print("❌ No verification result returned")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_verification_direct())
