#!/usr/bin/env python3
"""
Test available endpoints for CaseStrainer API
"""

import requests
import json

def test_endpoints():
    """Test various possible endpoints."""
    
    base_url = "http://localhost:5000"
    
    endpoints_to_test = [
        "/",
        "/api/analyze", 
        "/analyze",
        "/casestrainer/api/analyze",
        "/health",
        "/status"
    ]
    
    print("Testing CaseStrainer API endpoints...")
    print(f"Base URL: {base_url}")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            print(f"GET {endpoint:<25} -> {response.status_code} {response.reason}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"   JSON keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    except:
                        print(f"   Content length: {len(response.text)} chars")
                else:
                    print(f"   Content type: {content_type}")
                    if len(response.text) < 200:
                        print(f"   Content: {response.text[:100]}...")
            
        except requests.RequestException as e:
            print(f"GET {endpoint:<25} -> ERROR: {e}")
        
        print()
    
    # Test POST to analyze endpoints
    test_data = {
        'text': 'Test citation 2006 WL 3801910',
        'type': 'text'
    }
    
    analyze_endpoints = ["/api/analyze", "/analyze", "/casestrainer/api/analyze"]
    
    print("Testing POST to analyze endpoints...")
    print("=" * 50)
    
    for endpoint in analyze_endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.post(url, data=test_data, timeout=10)
            print(f"POST {endpoint:<25} -> {response.status_code} {response.reason}")
            
            if response.status_code in [200, 202]:
                try:
                    data = response.json()
                    print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    if 'task_id' in data:
                        print(f"   Task ID: {data['task_id']}")
                    if 'citations' in data:
                        print(f"   Citations found: {len(data['citations'])}")
                except:
                    print(f"   Content: {response.text[:200]}...")
            
        except requests.RequestException as e:
            print(f"POST {endpoint:<25} -> ERROR: {e}")
        
        print()

if __name__ == "__main__":
    test_endpoints()
