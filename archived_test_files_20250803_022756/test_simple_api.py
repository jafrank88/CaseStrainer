#!/usr/bin/env python3
"""
Simple API test to check if the backend is responding
"""

import requests
import json

def test_simple_api():
    """Test simple API requests"""
    
    print("🧪 Simple API Test")
    print("=" * 40)
    
    # Test health endpoint first
    health_url = "http://localhost:5000/casestrainer/api/health"
    print(f"🌐 Testing health endpoint: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        print(f"📥 Health Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"📄 Response: {response.text}")
        else:
            print(f"❌ Health check failed: {response.text}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    print("\n" + "=" * 40)
    
    # Test simple text analysis
    analyze_url = "http://localhost:5000/casestrainer/api/analyze"
    print(f"🌐 Testing text analysis: {analyze_url}")
    
    test_data = {
        "text": "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "document_type": "test"
    }
    
    try:
        response = requests.post(
            analyze_url, 
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"📥 Analysis Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Text analysis passed!")
            result = response.json()
            print(f"📊 Citations found: {len(result.get('citations', []))}")
        else:
            print(f"❌ Text analysis failed: {response.text}")
    except Exception as e:
        print(f"❌ Text analysis error: {e}")
    
    print("=" * 40)

if __name__ == "__main__":
    test_simple_api() 