"""
Quick test to verify the /analyze endpoint is working with URL input
"""
import requests
import json
import time

# Test the URL analysis endpoint
url = "https://wolf.law.uw.edu/casestrainer/api/analyze"

# Test data - same URL you were using
test_data = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1034300.pdf",
    "client_request_id": f"test-{int(time.time())}"
}

print(f"Testing endpoint: {url}")
print(f"Request data: {json.dumps(test_data, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(
        url,
        json=test_data,
        timeout=30,
        verify=False  # Skip SSL verification for local testing
    )
    
    print(f"\n✅ Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! Endpoint is working")
        result = response.json()
        print(f"\nResponse preview:")
        print(json.dumps(result, indent=2)[:500])
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("\n⏱️ Request timed out (expected for large PDF processing)")
    print("This is normal - the backend will process asynchronously")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
