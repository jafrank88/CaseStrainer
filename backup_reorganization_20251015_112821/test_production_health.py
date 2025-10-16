"""
Test Production Health and Available Endpoints
"""
import requests
import json

print("=" * 100)
print("PRODUCTION HEALTH CHECK")
print("=" * 100)

# Test basic health
urls = [
    "http://localhost:5000/",
    "http://localhost:5000/api/health",
    "http://localhost:5000/api/v2/health",
    "http://localhost:5000/api/extract",
]

for url in urls:
    try:
        print(f"\n🔍 Testing: {url}")
        response = requests.get(url, timeout=5)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=4)}")
            except:
                print(f"   Response (text): {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 100)
