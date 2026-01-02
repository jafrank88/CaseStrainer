#!/usr/bin/env python3
"""
Test Law Resource.org verification directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_verification_master import UnifiedVerificationMaster

async def test_law_resource_direct():
    """Test Law Resource.org verification directly"""
    
    print("🧪 Testing Law Resource.org verification directly...")
    
    # Initialize the verification master
    verifier = UnifiedVerificationMaster()
    
    # Test with the citation we know exists
    citation = "161 F.3d 584"
    extracted_case_name = "In Smith v. Jones"  # Use the extracted name from our test
    extracted_date = None
    timeout = 10.0
    
    print(f"📋 Citation: {citation}")
    print(f"👥 Case name: {extracted_case_name}")
    
    try:
        # Call the verification method directly
        result = await verifier._verify_with_law_resource(
            citation, extracted_case_name, extracted_date, timeout
        )
        
        print(f"\n📊 Verification Result:")
        print(f"   Verified: {result.verified}")
        print(f"   Source: {result.source}")
        print(f"   Canonical Name: {result.canonical_name}")
        print(f"   Canonical URL: {result.canonical_url}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Method: {result.method}")
        print(f"   Error: {result.error}")
        
        if result.verified:
            print(f"\n✅ SUCCESS: Law Resource.org verification works!")
            return True
        else:
            print(f"\n❌ FAILURE: Law Resource.org verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_law_resource_direct())
    
    if success:
        print("\n✅ Law Resource.org verification is working!")
    else:
        print("\n❌ Law Resource.org verification has issues")
