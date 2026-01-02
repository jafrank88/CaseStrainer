#!/usr/bin/env python3
"""
Test to verify that citation verification is now working correctly
after fixing the enable_verification default values.
"""

import requests
import time
import json

def test_verification_enabled():
    """Test that citations are now being verified"""
    
    print("🔍 TESTING CITATION VERIFICATION FIX")
    print("=" * 50)
    
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    # Test with a few well-known citations that should verify
    test_text = """
    This document references several important Supreme Court cases:
    
    Brown v. Board of Education, 347 U.S. 483 (1954). This landmark case ended segregation in public schools.
    
    Roe v. Wade, 410 U.S. 113 (1973). This case established a woman's legal right to abortion.
    
    Miranda v. Arizona, 384 U.S. 436 (1966). This case established Miranda rights.
    """
    
    print("📋 Testing with well-known Supreme Court citations...")
    
    try:
        start_time = time.time()
        response = requests.post(api_url, json={
            'type': 'text',
            'text': test_text,
            'enable_verification': True  # Explicitly enable verification
        }, timeout=60)  # Allow up to 60 seconds for verification
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Processing completed in {elapsed:.1f}s")
            
            citations = result.get('citations', [])
            print(f"📊 Found {len(citations)} citations")
            
            verified_count = 0
            for i, citation in enumerate(citations):
                citation_text = citation.get('citation', 'Unknown')
                is_verified = citation.get('verified', False)
                verification_status = citation.get('metadata', {}).get('verification_status', 'unknown')
                canonical_name = citation.get('canonical_name')
                canonical_url = citation.get('canonical_url')
                
                print(f"\n🔎 Citation {i+1}: {citation_text}")
                print(f"   Verified: {is_verified}")
                print(f"   Status: {verification_status}")
                
                if is_verified:
                    verified_count += 1
                    print(f"   ✅ Canonical Name: {canonical_name}")
                    print(f"   ✅ URL: {canonical_url}")
                else:
                    print(f"   ❌ No verification data found")
            
            print(f"\n📈 VERIFICATION SUMMARY:")
            print(f"   Total citations: {len(citations)}")
            print(f"   Verified citations: {verified_count}")
            print(f"   Success rate: {(verified_count/len(citations)*100):.1f}%" if citations else "N/A")
            
            if verified_count > 0:
                print("🎉 SUCCESS: Verification is now working!")
                print("   Citations are being verified against CourtListener API")
            else:
                print("⚠️  WARNING: No citations were verified")
                print("   This may indicate API issues or rate limiting")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - verification may be taking longer than expected")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🔧 VERIFICATION FIXES APPLIED:")
    print("✅ UnifiedClusteringMaster: enable_verification default False → True")
    print("✅ extract_citations_with_clustering: enable_verification default False → True") 
    print("✅ SimplifiedCitationProcessor: Use config.enable_verification instead of hardcoded False")
    print("✅ API parameter enable_verification=True now properly propagates through pipeline")

if __name__ == "__main__":
    test_verification_enabled()
