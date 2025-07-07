#!/usr/bin/env python3
"""
Test the citation processing API endpoint
"""

import requests
import json
import time

def test_citation_processing():
    """Test the citation processing endpoint with a simple citation."""
    
    url = "http://localhost:5000/casestrainer/api/process-text"
    
    # Test data with a Washington citation
    test_data = {
        "text": "See State v. Lewis, 115 Wn.2d 294, 298-99, 797 P.2d 1141 (1990).",
        "extract_case_names": True,
        "include_context": True
    }
    
    print("Testing citation processing API...")
    print(f"URL: {url}")
    print(f"Test data: {json.dumps(test_data, indent=2)}")
    print("-" * 50)
    
    try:
        # Make the request
        response = requests.post(url, json=test_data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS: Citation processing worked!")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check if citations were found
            if 'citations' in result:
                print(f"Found {len(result['citations'])} citations")
                for i, citation in enumerate(result['citations']):
                    print(f"  Citation {i+1}: {citation}")
            
            # Check if case names were extracted
            if 'case_names' in result:
                print(f"Found {len(result['case_names'])} case names")
                for i, case_name in enumerate(result['case_names']):
                    print(f"  Case name {i+1}: {case_name}")
                    
        else:
            print(f"❌ ERROR: Status code {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT: Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Could not connect to the server")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_citation_processing() 