#!/usr/bin/env python3
"""
Debug script to check exactly what the API is returning
"""

import requests
import json

def debug_api_response():
    """Debug the API response to see what fields are actually being returned"""
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Test data with Washington citation
    test_data = {
        "type": "text",
        "text": "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions",
        "citations": ["200 Wn.2d 72, 514 P.3d 643"]
    }
    
    print("🔍 DEBUGGING API RESPONSE...")
    print(f"URL: {url}")
    print(f"Request data: {json.dumps(test_data, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response Structure:")
            print(json.dumps(result, indent=2))
            
            # Check if we got citations
            if 'citations' in result and result['citations']:
                citation_result = result['citations'][0]
                print("\n🔍 CITATION RESULT ANALYSIS:")
                print(f"All keys in citation: {list(citation_result.keys())}")
                print()
                
                # Check extracted fields
                print("📋 EXTRACTED FIELDS:")
                print(f"extracted_case_name: '{citation_result.get('extracted_case_name', 'NOT_FOUND')}'")
                print(f"extracted_date: '{citation_result.get('extracted_date', 'NOT_FOUND')}'")
                print(f"case_name: '{citation_result.get('case_name', 'NOT_FOUND')}'")
                print()
                
                # Check canonical fields
                print("📋 CANONICAL FIELDS:")
                print(f"canonical_name: '{citation_result.get('canonical_name', 'NOT_FOUND')}'")
                print(f"canonical_date: '{citation_result.get('canonical_date', 'NOT_FOUND')}'")
                print()
                
                # Check other fields
                print("📋 OTHER FIELDS:")
                print(f"verified: '{citation_result.get('verified', 'NOT_FOUND')}'")
                print(f"source: '{citation_result.get('source', 'NOT_FOUND')}'")
                print(f"method: '{citation_result.get('method', 'NOT_FOUND')}'")
                print(f"citation: '{citation_result.get('citation', 'NOT_FOUND')}'")
                print()
                
                # Check if fields are null, empty, or "N/A"
                extracted_name = citation_result.get('extracted_case_name')
                extracted_date = citation_result.get('extracted_date')
                
                print("🔍 FIELD ANALYSIS:")
                print(f"extracted_case_name type: {type(extracted_name)}")
                print(f"extracted_case_name value: '{extracted_name}'")
                print(f"extracted_case_name is None: {extracted_name is None}")
                print(f"extracted_case_name == 'N/A': {extracted_name == 'N/A'}")
                print(f"extracted_case_name == '': {extracted_name == ''}")
                print()
                print(f"extracted_date type: {type(extracted_date)}")
                print(f"extracted_date value: '{extracted_date}'")
                print(f"extracted_date is None: {extracted_date is None}")
                print(f"extracted_date == 'N/A': {extracted_date == 'N/A'}")
                print(f"extracted_date == '': {extracted_date == ''}")
                
            else:
                print("⚠️  No citations found in response")
                print(f"Response keys: {list(result.keys())}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Flask server not running or not accessible")
        print("Make sure the Flask server is running on localhost:5000")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    debug_api_response() 