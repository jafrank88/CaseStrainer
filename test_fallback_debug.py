#!/usr/bin/env python3
"""
Comprehensive test script to debug fallback verification failures
"""

import requests
import json
import time

def test_fallback_sources():
    """Test each fallback source individually to see what's happening"""
    
    # Test citations that should be found
    test_citations = [
        "188 Wn.2d 114",      # In re Marriage of Black
        "392 P.3d 1041",      # In re Marriage of Black (parallel)
        "178 Wn. App. 929",   # In re Vulnerable Adult Petition for Knight
        "317 P.3d 1068",      # In re Vulnerable Adult Petition for Knight (parallel)
        "230 P.3d 233",       # Blackmon v. Blackmon (known to work)
        "155 Wn. App. 715"    # Blackmon v. Blackmon (known to work)
    ]
    
    print("🔍 Testing Fallback Verification Sources")
    print("=" * 60)
    
    for citation in test_citations:
        print(f"\n📋 Testing Citation: {citation}")
        print("-" * 40)
        
        try:
            # Test the API endpoint
            url = "http://localhost:5000/casestrainer/api/analyze"
            payload = {
                "text": f"Case: {citation}",
                "type": "text"
            }
            
            print(f"📡 Sending request to: {url}")
            response = requests.post(url, json=payload, timeout=30)
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                citations = result.get('result', {}).get('citations', [])
                
                if citations:
                    citation_data = citations[0]
                    print(f"✅ Found citation data:")
                    print(f"  Verified: {citation_data.get('verified', 'N/A')}")
                    print(f"  Case Name: {citation_data.get('case_name', 'N/A')}")
                    print(f"  Canonical Name: {citation_data.get('canonical_name', 'N/A')}")
                    print(f"  Source: {citation_data.get('source', 'N/A')}")
                    
                    # Check metadata for verification details
                    if citation_data.get('metadata'):
                        print(f"  Metadata:")
                        for key, value in citation_data['metadata'].items():
                            if 'verification' in key.lower() or 'source' in key.lower():
                                print(f"    {key}: {value}")
                else:
                    print("❌ No citations found in response")
                    
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        # Small delay between requests
        time.sleep(1)
    
    print(f"\n🔍 Summary of Fallback Verification Results")
    print("=" * 60)
    print("Citations that should work:")
    print("  ✅ 230 P.3d 233 (Blackmon v. Blackmon)")
    print("  ✅ 155 Wn. App. 715 (Blackmon v. Blackmon)")
    print("\nCitations that aren't working:")
    print("  ❌ 188 Wn.2d 114 (In re Marriage of Black)")
    print("  ❌ 392 P.3d 1041 (In re Marriage of Black)")
    print("  ❌ 178 Wn. App. 929 (In re Vulnerable Adult Petition for Knight)")
    print("  ❌ 317 P.3d 1068 (In re Vulnerable Adult Petition for Knight)")
    
    print(f"\n💡 Possible reasons for failure:")
    print("  1. Citations don't exist in fallback databases")
    print("  2. Fallback sources have different citation formats")
    print("  3. Case names are too different from what's in databases")
    print("  4. Fallback verification is failing silently")

if __name__ == "__main__":
    test_fallback_sources()
