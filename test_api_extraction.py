#!/usr/bin/env python3
"""
Test the API endpoint to verify extracted fields are being returned
"""

import requests
import json

def test_api_extraction():
    """Test the /analyze endpoint with a simple citation"""
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Test data
    data = {
        "text": "Punx v Smithers, 534 F.3d 1290 (1921)",
        "citations": ["534 F.3d 1290"]
    }
    
    print("🔍 Testing API extraction...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(data, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response:")
            print(json.dumps(result, indent=2))
            
            # Check for extracted fields
            if 'citations' in result and result['citations']:
                citation = result['citations'][0]
                print("\n📋 Citation Details:")
                print(f"  extracted_case_name: '{citation.get('extracted_case_name', 'NOT_FOUND')}'")
                print(f"  extracted_date: '{citation.get('extracted_date', 'NOT_FOUND')}'")
                print(f"  case_name: '{citation.get('case_name', 'NOT_FOUND')}'")
                print(f"  year: '{citation.get('year', 'NOT_FOUND')}'")
                
                # Check if extraction worked
                if citation.get('extracted_case_name') and citation.get('extracted_case_name') != 'N/A':
                    print("✅ SUCCESS: extracted_case_name is present!")
                else:
                    print("❌ FAILED: extracted_case_name is missing or 'N/A'")
                    
                if citation.get('extracted_date') and citation.get('extracted_date') != 'N/A':
                    print("✅ SUCCESS: extracted_date is present!")
                else:
                    print("❌ FAILED: extracted_date is missing or 'N/A'")
            else:
                print("❌ No citations found in response")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend server not running or not accessible")
    except requests.exceptions.Timeout:
        print("❌ Timeout Error: Request took too long")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_extraction() 