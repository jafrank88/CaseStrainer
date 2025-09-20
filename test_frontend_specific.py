#!/usr/bin/env python3
"""
Test the exact same way the frontend calls the API to identify the difference.
"""

import requests
import json
import time

def test_frontend_exact_call():
    """Test exactly how the frontend calls the API."""
    
    print("🔍 Testing Frontend-Exact API Call")
    print("=" * 50)
    
    # Test with simple text first
    simple_text = "This case cites Brown v. Board of Education, 347 U.S. 483 (1954)."
    
    # Create FormData exactly like the frontend does
    formData = {
        'text': simple_text,
        'type': 'text'
    }
    
    # Use the exact endpoint and headers the frontend uses
    endpoint = "http://localhost:8080/casestrainer/api/analyze"
    headers = {
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        print(f"📤 Making request to: {endpoint}")
        print(f"📝 Data: {formData}")
        print(f"📋 Headers: {headers}")
        
        response = requests.post(endpoint, data=formData, headers=headers, timeout=30)
        
        print(f"\n📊 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code != 200:
            print(f"❌ Request failed!")
            print(f"Response text: {response.text}")
            return False
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"Raw response: {response.text[:500]}...")
            return False
        
        print(f"   Success: {data.get('success', False)}")
        print(f"   Processing mode: {data.get('metadata', {}).get('processing_mode', 'unknown')}")
        print(f"   Citations: {len(data.get('citations', []))}")
        print(f"   Clusters: {len(data.get('clusters', []))}")
        
        # Print the full structure to see what the frontend actually gets
        print(f"\n📋 Full Response Structure:")
        print(json.dumps(data, indent=2)[:1000] + "..." if len(json.dumps(data, indent=2)) > 1000 else json.dumps(data, indent=2))
        
        if len(data.get('citations', [])) == 0:
            print(f"\n❌ FRONTEND ISSUE CONFIRMED: No citations in response!")
            print(f"🔍 This is exactly what the frontend sees")
            return False
        else:
            print(f"\n✅ Frontend call working correctly")
            return True
            
    except Exception as e:
        print(f"💥 Frontend test error: {e}")
        return False

def test_different_request_methods():
    """Test different ways of making the request."""
    
    print(f"\n🔍 Testing Different Request Methods")
    print("=" * 50)
    
    simple_text = "This case cites Brown v. Board of Education, 347 U.S. 483 (1954)."
    endpoint = "http://localhost:8080/casestrainer/api/analyze"
    
    # Method 1: JSON payload (like our backend test)
    print(f"📤 Method 1: JSON payload")
    try:
        response1 = requests.post(endpoint, json={"text": simple_text, "type": "text"}, timeout=30)
        print(f"   Status: {response1.status_code}")
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"   Citations: {len(data1.get('citations', []))}")
        else:
            print(f"   Error: {response1.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 2: FormData (like frontend)
    print(f"\n📤 Method 2: FormData")
    try:
        response2 = requests.post(endpoint, data={"text": simple_text, "type": "text"}, timeout=30)
        print(f"   Status: {response2.status_code}")
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"   Citations: {len(data2.get('citations', []))}")
        else:
            print(f"   Error: {response2.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 3: FormData with files parameter (multipart)
    print(f"\n📤 Method 3: Multipart FormData")
    try:
        files = {'text': (None, simple_text), 'type': (None, 'text')}
        response3 = requests.post(endpoint, files=files, timeout=30)
        print(f"   Status: {response3.status_code}")
        if response3.status_code == 200:
            data3 = response3.json()
            print(f"   Citations: {len(data3.get('citations', []))}")
        else:
            print(f"   Error: {response3.text[:200]}")
    except Exception as e:
        print(f"   Exception: {e}")

def main():
    """Test frontend-specific issues."""
    
    print("🚀 Frontend-Specific Issue Diagnosis")
    print("=" * 60)
    
    # Test exact frontend call
    frontend_ok = test_frontend_exact_call()
    
    # Test different request methods
    test_different_request_methods()
    
    print("\n" + "=" * 60)
    print("📋 FRONTEND DIAGNOSIS RESULTS")
    print("=" * 60)
    
    if frontend_ok:
        print("✅ Frontend API call is working")
        print("🔍 Issue might be in frontend JavaScript processing")
    else:
        print("❌ Frontend API call is failing")
        print("🔧 Issue is in the API endpoint or request format")
        print("💡 Check the different request methods above")
    
    return frontend_ok

if __name__ == "__main__":
    main()
