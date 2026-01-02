#!/usr/bin/env python3
"""
Test script to check verification pipeline with debug logging
"""

import requests
import json

def test_verification_pipeline():
    """Test the verification pipeline with debug logging"""
    
    # Simple test text with a known verifiable citation
    test_text = "The Supreme Court decision in 521 U.S. 811 established important precedent."
    
    print("🔍 Testing verification pipeline with debug logging")
    print(f"Test text: {test_text}")
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        "text": test_text,
        "type": "text"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📋 Full response structure:")
            print(f"   Response keys: {list(result.keys())}")
            
            # Check different possible locations for citations
            citations = []
            if 'citations' in result:
                citations = result['citations']
                print(f"   Found citations at top level: {len(citations)}")
            elif 'result' in result:
                if isinstance(result['result'], dict):
                    if 'citations' in result['result']:
                        citations = result['result']['citations']
                        print(f"   Found citations in result.citations: {len(citations)}")
                    elif 'result' in result['result'] and 'citations' in result['result']['result']:
                        citations = result['result']['result']['citations']
                        print(f"   Found citations in result.result.citations: {len(citations)}")
            
            print(f"\n📋 Final citations count: {len(citations)}")
            
            for i, citation in enumerate(citations):
                print(f"\n  Citation {i+1}: {citation.get('citation', 'N/A')}")
                print(f"    Verified: {citation.get('verified', 'N/A')}")
                print(f"    Canonical Name: {citation.get('canonical_name', 'N/A')}")
                print(f"    Canonical Date: {citation.get('canonical_date', 'N/A')}")
                print(f"    Canonical URL: {citation.get('canonical_url', 'N/A')}")
                print(f"    Verification Status: {citation.get('verification_status', 'N/A')}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_verification_pipeline()
