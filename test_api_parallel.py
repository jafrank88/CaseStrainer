#!/usr/bin/env python3
"""
Test parallel verification through API
"""

import requests
import time
import json

def test_api_parallel():
    """Test parallel citation verification through API"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    
    # Simple test text with clear parallel citations
    test_text = "Gresser v. Banner Health, 2023 COA 108, 543 P.3d 1059."
    
    print(f"Testing parallel verification through API...")
    print(f"Text: {test_text}")
    
    data = {
        'text': test_text,
        'client_request_id': f'parallel-test-{int(time.time())}',
        'force_mode': 'sync'  # Force sync to see immediate results
    }
    
    try:
        response = requests.post(f"{base_url}/analyze", data=data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            
            print(f"\n✅ API returned {len(citations)} citations:")
            
            for i, cit in enumerate(citations):
                citation_text = cit.get('citation', 'N/A')
                verified = cit.get('verified', False)
                true_by_parallel = cit.get('true_by_parallel', False)
                canonical_name = cit.get('canonical_name', 'N/A')
                
                print(f"\n{i+1}. {citation_text}")
                print(f"   verified: {verified}")
                print(f"   true_by_parallel: {true_by_parallel}")
                print(f"   canonical_name: {canonical_name[:50]}..." if len(canonical_name) > 50 else f"   canonical_name: {canonical_name}")
            
            # Check if parallel verification worked
            parallel_verified = [cit for cit in citations if cit.get('true_by_parallel', False)]
            directly_verified = [cit for cit in citations if cit.get('verified', False) == True]
            
            print(f"\n📊 Verification Summary:")
            print(f"   Directly verified: {len(directly_verified)}")
            print(f"   Verified by parallel: {len(parallel_verified)}")
            print(f"   Total verified: {len(directly_verified) + len(parallel_verified)}")
            
            if len(parallel_verified) > 0:
                print(f"\n✅ Parallel verification is working in API!")
            else:
                print(f"\n❌ Parallel verification is not working in API.")
            
        else:
            print(f"❌ API call failed: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_parallel()
