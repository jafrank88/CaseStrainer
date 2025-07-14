#!/usr/bin/env python3
"""
Test the live URL decoder functionality
"""

import requests
import json

def test_live_url_decoder():
    """Test the URL decoder with the live API"""
    
    print("🧪 Testing Live URL Decoder")
    print("=" * 50)
    
    # Test the Microsoft Defender URL
    encoded_url = "https://urldefense.com/v3/__https://case.law/caselaw/?reporter=cal-4th%26volume=11%26case=0001-01__;!!K-Hz7m0Vt54!lcqn6knCAosua6gJk8AC4Q-17TrHwdDGnxO86ki22fEQBKpNSGM5q48EYTTPvEFv1lxsoN7NKcodFOvFuXI$"
    
    print(f"Testing encoded URL: {encoded_url[:80]}...")
    
    # Test the API endpoint
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    payload = {
        "type": "url",
        "url": encoded_url
    }
    
    try:
        print("Sending request to API...")
        response = requests.post(api_url, json=payload, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API request successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Check if the URL was decoded
            if 'metadata' in data and 'source_name' in data['metadata']:
                decoded_url = data['metadata']['source_name']
                print(f"Decoded URL: {decoded_url}")
                
                if "case.law" in decoded_url and "urldefense.com" not in decoded_url:
                    print("✅ URL was successfully decoded!")
                    return True
                else:
                    print("❌ URL was not decoded properly")
                    return False
            else:
                print("❌ No metadata found in response")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    success = test_live_url_decoder()
    
    if success:
        print("\n🎉 URL decoder is working in the live system!")
        print("Users can now paste Microsoft Defender URLs directly into CaseStrainer.")
    else:
        print("\n❌ URL decoder needs investigation.") 