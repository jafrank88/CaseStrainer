#!/usr/bin/env python3
"""Test the API endpoint to see if it's calling the extraction function correctly"""

import requests
import json

def test_api_endpoint():
    # Test the actual API endpoint
    url = "http://localhost:5000/casestrainer/api/analyze_enhanced"
    data = {
        "type": "text",
        "text": "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions",
        "citations": ["200 Wn.2d 72, 73, 514 P.3d 643"]
    }

    print("🧪 Testing API endpoint...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.content:
            try:
                response_json = response.json()
                print(f"\n📋 Response JSON:")
                print(json.dumps(response_json, indent=2))
                
                # Check specific fields
                if 'citations' in response_json and response_json['citations']:
                    citation = response_json['citations'][0]
                    print(f"\n🔍 FIELD ANALYSIS:")
                    print(f"  extracted_case_name: '{citation.get('extracted_case_name', 'MISSING')}'")
                    print(f"  extracted_date: '{citation.get('extracted_date', 'MISSING')}'")
                    print(f"  canonical_name: '{citation.get('canonical_name', 'MISSING')}'")
                    print(f"  canonical_date: '{citation.get('canonical_date', 'MISSING')}'")
                    print(f"  verified: '{citation.get('verified', 'MISSING')}'")
                    
                    # Success analysis
                    extracted_name_ok = citation.get('extracted_case_name') == 'EXTRACTED_FAKE_NAME_Y'
                    extracted_date_ok = citation.get('extracted_date') == '2099-12-31'
                    
                    print(f"\n✅ SUCCESS ANALYSIS:")
                    print(f"  extracted_case_name correct: {extracted_name_ok}")
                    print(f"  extracted_date correct: {extracted_date_ok}")
                    
                    if extracted_name_ok and extracted_date_ok:
                        print("\n🎉 SUCCESS! API is working correctly with fake data!")
                    else:
                        print("\n❌ API is not returning the expected fake data values")
                        
                else:
                    print("❌ No citations found in response")
                    
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON Response: {response.text}")
        else:
            print("❌ Empty response")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the Flask server is running on localhost:5000")
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_endpoint() 