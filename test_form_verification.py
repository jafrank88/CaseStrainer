#!/usr/bin/env python3
"""Test form data with enable_verification=false parameter"""

import requests
import json

def test_form_data():
    """Test with form data"""
    
    print("Testing with form data and enable_verification=false...")
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Test with form data
    form_data = {
        "text": "Johnson v. United States, 888 F.3d 123 (2024). This is a new test case.",
        "type": "text",
        "enable_verification": "false"
    }
    
    try:
        # Test with form data
        response = requests.post(
            f"{base_url}/analyze",
            data=form_data,
            timeout=30
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            
            print(f"✅ Success! Found {len(citations)} citations and {len(clusters)} clusters")
            
            # Check if citations are verified
            verified_count = sum(1 for c in citations if c.get('verified', False))
            print(f"Verified citations: {verified_count}/{len(citations)}")
            
            # Print first citation details
            if citations:
                first = citations[0]
                print(f"\nFirst citation:")
                print(f"  Citation: {first.get('citation', 'N/A')}")
                print(f"  Verified: {first.get('verified', False)}")
                print(f"  Source: {first.get('source', 'N/A')}")
                print(f"  Processing time: {data.get('metadata', {}).get('processing_time_ms', 'N/A')}ms")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (30s)")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_form_data()
