#!/usr/bin/env python3
"""Test the Docker production API to see if the extraction is working"""

import requests
import json

def test_docker_api():
    # Test the Docker production API endpoint
    # Try different possible URLs for Docker setup
    possible_urls = [
        "http://localhost:5000/casestrainer/api/analyze_enhanced",
        "http://localhost:80/casestrainer/api/analyze_enhanced", 
        "http://localhost/casestrainer/api/analyze_enhanced",
        "http://127.0.0.1:5000/casestrainer/api/analyze_enhanced"
    ]
    
    data = {
        "type": "text",
        "text": "The court considered the case of Doe v. Wdae, 410 U.S. 113 (1901) in determining the outcome.",
        "citations": ["Doe v. Wdae, 410 U.S. 113 (1901)"]
    }

    print("Testing Docker Production API...")
    print(f"Data: {json.dumps(data, indent=2)}")
    print()

    for url in possible_urls:
        print(f"Testing URL: {url}")
        try:
            response = requests.post(url, json=data, timeout=10)
            print(f"✅ SUCCESS! Status: {response.status_code}")
            
            if response.content:
                try:
                    response_json = response.json()
                    print(f"Response JSON:")
                    print(json.dumps(response_json, indent=2))
                    
                    # Check specific fields
                    if 'citations' in response_json and response_json['citations']:
                        citation = response_json['citations'][0]
                        print(f"\n🔍 FIELD ANALYSIS:")
                        print(f"  extracted_case_name: '{citation.get('extracted_case_name', 'MISSING')}'")
                        print(f"  extracted_date: '{citation.get('extracted_date', 'MISSING')}'")
                        print(f"  canonical_name: '{citation.get('canonical_name', 'MISSING')}'")
                        print(f"  canonical_date: '{citation.get('canonical_date', 'MISSING')}'")
                        
                        # Check if the mapping worked
                        if citation.get('extracted_case_name') == 'EXTRACTED_FAKE_NAME_Y':
                            print("✅ SUCCESS: extracted_case_name mapped correctly!")
                        else:
                            print(f"❌ FAILED: extracted_case_name is '{citation.get('extracted_case_name')}' instead of 'EXTRACTED_FAKE_NAME_Y'")
                            
                        if citation.get('extracted_date') == '2099-12-31':
                            print("✅ SUCCESS: extracted_date mapped correctly!")
                        else:
                            print(f"❌ FAILED: extracted_date is '{citation.get('extracted_date')}' instead of '2099-12-31'")
                    else:
                        print("❌ No citations found in response")
                        
                except json.JSONDecodeError:
                    print(f"Response Text: {response.text}")
            else:
                print("Empty response")
                
            # If we get here, we found a working URL
            break
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed")
        except requests.exceptions.Timeout:
            print(f"❌ Request timed out")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_docker_api() 