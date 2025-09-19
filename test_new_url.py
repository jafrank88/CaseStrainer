#!/usr/bin/env python3
"""
Test the new URL provided by the user.
"""

import requests

def test_new_url():
    """Test the new URL to see if it works."""
    
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    print("🔗 Testing New URL")
    print("=" * 60)
    print(f"📄 URL: {test_url}")
    print()
    
    # Test 1: Direct access
    print("🧪 Test 1: Direct URL Access")
    try:
        response = requests.head(test_url, timeout=10)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"  Content-Length: {response.headers.get('Content-Length', 'N/A')}")
        
        if response.status_code == 200:
            print("  ✅ URL is accessible")
        else:
            print(f"  ❌ URL returned status {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ URL access failed: {e}")
    
    # Test 2: API processing
    print(f"\n🧪 Test 2: API Processing")
    try:
        api_response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"url": test_url},
            timeout=60
        )
        
        print(f"  API Status: {api_response.status_code}")
        
        if api_response.status_code == 200:
            data = api_response.json()
            print(f"  Success: {data.get('success')}")
            print(f"  Citations: {len(data.get('citations', []))}")
            print(f"  Message: {data.get('message')}")
            
            if data.get('task_id'):
                print(f"  Task ID: {data['task_id']}")
                print("  ✅ URL queued for async processing")
            else:
                print("  ✅ URL processed synchronously")
                
        elif api_response.status_code == 400:
            try:
                error_data = api_response.json()
                print(f"  Error: {error_data.get('error', 'No error message')}")
            except:
                print(f"  Raw error: {api_response.text[:200]}...")
        else:
            print(f"  Unexpected status: {api_response.status_code}")
            print(f"  Response: {api_response.text[:200]}...")
            
    except Exception as e:
        print(f"  ❌ API test failed: {e}")

if __name__ == "__main__":
    test_new_url()
