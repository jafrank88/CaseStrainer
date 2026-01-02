#!/usr/bin/env python3
"""
Test small text with forced sync processing
"""

import requests
import time

def test_small_sync():
    """Test small text with forced sync processing"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    
    # Small text with U.S. citation
    test_text = "This is a test case with citation 463 U.S. 29 and another one 390 U.S. 747."
    
    print(f"Testing small text with forced sync processing...")
    print(f"Text: {test_text}")
    
    # Prepare request
    data = {
        "type": "text",
        "text": test_text,
        "force_mode": "sync"
    }
    
    print(f"\n=== Sending Request ===")
    
    try:
        response = requests.post(f"{base_url}/analyze", json=data)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.text}")
            return
        
        result = response.json()
        request_id = result.get('request_id')
        
        print(f"✅ Request successful")
        print(f"Request ID: {request_id}")
        print(f"Success: {result.get('success')}")
        print(f"Processing strategy: {result.get('processing_strategy')}")
        
        # Check citations
        citations = result.get('citations', [])
        print(f"Citations returned: {len(citations)}")
        
        if citations:
            print(f"Citations found:")
            for i, cit in enumerate(citations):
                print(f"  {i+1}. {cit}")
        else:
            print("No citations in immediate response")
        
        # If async, check final results
        if result.get('processing_strategy') != 'immediate':
            print(f"\n=== Getting Final Results ===")
            final_response = requests.get(f"{base_url}/analyze/verification-status/{request_id}")
            
            if final_response.status_code == 200:
                final_result = final_response.json()
                final_citations = final_result.get('citations', [])
                print(f"Final citations: {len(final_citations)}")
                
                if final_citations:
                    for i, cit in enumerate(final_citations):
                        print(f"  {i+1}. {cit}")
            else:
                print(f"❌ Failed to get final results: {final_response.status_code}")
        
    except Exception as e:
        print(f"❌ Error during request: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_small_sync()
