#!/usr/bin/env python3
"""
Test that the frontend now calls the working /analyze_enhanced endpoint
"""

import requests
import json

def test_frontend_endpoint():
    """Test that the frontend endpoint now works with extracted fields"""
    
    url = "http://localhost:5000/casestrainer/api/analyze_enhanced"
    
    # Test data with Washington citation (same as frontend would send)
    test_data = {
        "type": "text",
        "text": "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions",
        "citations": ["200 Wn.2d 72, 514 P.3d 643"]
    }
    
    print("🧪 Testing frontend endpoint change...")
    print(f"URL: {url}")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Frontend endpoint working:")
            print(json.dumps(result, indent=2))
            
            # Check if we got real extracted data
            if 'results' in result and result['results']:
                citation_result = result['results'][0]
                print("\n🔍 EXTRACTION ANALYSIS:")
                print(f"Extracted case name: '{citation_result.get('extracted_case_name', 'N/A')}'")
                print(f"Extracted date: '{citation_result.get('extracted_date', 'N/A')}'")
                print(f"Canonical name: '{citation_result.get('canonical_name', 'N/A')}'")
                print(f"Canonical date: '{citation_result.get('canonical_date', 'N/A')}'")
                
                # Check if we got real extraction vs N/A
                extracted_name = citation_result.get('extracted_case_name', 'N/A')
                extracted_date = citation_result.get('extracted_date', 'N/A')
                
                if extracted_name != 'N/A' and extracted_date != 'N/A':
                    print("🎉 FRONTEND ENDPOINT CHANGE SUCCESSFUL!")
                    print("✅ Your frontend will now receive extracted fields!")
                else:
                    print("⚠️  Extraction still returned N/A - may need investigation")
            else:
                print("⚠️  No results found in response")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Flask server not running or not accessible")
        print("Make sure the Flask server is running on localhost:5000")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_frontend_endpoint() 