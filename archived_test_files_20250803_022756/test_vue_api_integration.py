"""
Test script to verify Vue API integration in the running application
"""
import sys
import os
import requests
import json

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_vue_api_integration():
    """Test Vue API integration in the running application"""
    print("=== TESTING VUE API INTEGRATION ===\n")
    
    # 1. Test health endpoint
    print("1. Testing health endpoint...")
    try:
        response = requests.get("http://localhost:5000/casestrainer/api/health")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.headers.get('content-type')}")
        print("\n   Response Body:")
        print(f"   {json.dumps(response.json(), indent=2)}")
        
        # Check if this is the debug or Vue API
        if "Debug API" in response.text:
            print("\n⚠️  WARNING: Debug API is still active!")
            print("   This should not happen in production.")
        else:
            print("\n✅ Vue API is responding to health check")
            
    except Exception as e:
        print(f"\n❌ Error testing health endpoint: {e}")
    
    # 2. Test analyze endpoint with a test citation
    print("\n2. Testing analyze endpoint...")
    try:
        test_data = {
            "text": "This is a test citation to City of Seattle v. Ratliff, 100 Wn.2d 212 (1983)"
        }
        
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.headers.get('content-type')}")
        
        # Print the response body if it's JSON
        if "application/json" in response.headers.get('content-type', ''):
            print("\n   Response Body:")
            print(f"   {json.dumps(response.json(), indent=2)}")
        else:
            print("\n   Response Body:")
            print(f"   {response.text[:500]}...")
            
    except Exception as e:
        print(f"\n❌ Error testing analyze endpoint: {e}")
    
    # 3. Check registered routes
    print("\n3. Checking registered routes...")
    try:
        response = requests.get("http://localhost:5000/casestrainer/api/routes")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.headers.get('content-type')}")
        
        # Print the response body if it's JSON
        if "application/json" in response.headers.get('content-type', ''):
            print("\n   Response Body:")
            print(f"   {json.dumps(response.json(), indent=2)}")
        else:
            print("\n   Response Body:")
            print(f"   {response.text[:500]}...")
            
    except Exception as e:
        print(f"\n❌ Error checking registered routes: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_vue_api_integration()
