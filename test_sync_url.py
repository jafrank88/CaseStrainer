#!/usr/bin/env python3
"""
Test URL processing in sync mode to bypass async issues
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import requests
import json

def test_sync_url():
    """Test URL with force_mode=sync to bypass async processing."""
    url = "https://law.justia.com/cases/federal/us/390/747/"
    
    print(f"Testing sync processing for: {url}")
    
    # Try with force_mode=sync
    data = {
        'url': url,
        'force_mode': 'sync'
    }
    
    response = requests.post(
        "https://wolf.law.uw.edu/casestrainer/api/analyze",
        data=data,
        timeout=60,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print("✅ SUCCESS: Got direct response")
            print(f"Response keys: {list(result.keys())}")
            
            if 'citations' in result:
                citations = result['citations']
                print(f"Found {len(citations)} citations:")
                for i, citation in enumerate(citations[:5]):
                    print(f"  {i+1}. {citation.get('citation_text', 'N/A')} -> {citation.get('extracted_case_name', 'N/A')}")
            
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print(f"Raw response: {response.text[:500]}...")
            return False
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Error response: {response.text}")
        return False

if __name__ == "__main__":
    success = test_sync_url()
    sys.exit(0 if success else 1)
