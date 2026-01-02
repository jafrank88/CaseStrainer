#!/usr/bin/env python3
"""
Test the raw API response to see if citations are being returned
"""

import requests
import json

def test_api_raw_response():
    """Test API to see raw response data"""
    
    print("🔍 TESTING RAW API RESPONSE")
    print("=" * 40)
    
    simple_document = """
    The court considered precedent from Smith v. Jones, 123 U.S. 456 (2020) 
    and also referenced Brown v. Board, 345 F.2d 789 (2019).
    """
    
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    try:
        response = requests.post(
            api_url,
            json={"text": simple_document},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print("Raw response keys:", list(result.keys()))
            print()
            
            # Check citations
            citations = result.get('citations', [])
            print(f"Citations in response: {len(citations)}")
            
            # Check for validation warnings
            metadata = result.get('metadata', {})
            validation_warnings = metadata.get('validation_warnings', [])
            
            if validation_warnings:
                print(f"Validation warnings: {len(validation_warnings)}")
                for warning in validation_warnings[:3]:  # Show first 3
                    print(f"  - {warning}")
            else:
                print("No validation warnings")
            
            print()
            print("Full response structure:")
            print(json.dumps(result, indent=2)[:2000] + "..." if len(json.dumps(result)) > 2000 else json.dumps(result, indent=2))
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_raw_response()
