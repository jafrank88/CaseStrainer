"""
Test script to verify Vue API endpoint directly
"""
import sys
import os
import json
import requests

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Test the Vue API health endpoint
def test_vue_api_health():
    """Test the Vue API health endpoint"""
    print("\n=== TESTING VUE API HEALTH ENDPOINT ===")
    
    # Try to import the Vue API blueprint directly
    try:
        print("\nAttempting to import Vue API blueprint...")
        from src.vue_api_endpoints import vue_api
        print(f"✅ Successfully imported Vue API blueprint: {vue_api}")
        print(f"- Name: {vue_api.name}")
        print(f"- Import Name: {vue_api.import_name}")
        
        # Check if the health endpoint is registered
        print("\nChecking registered routes:")
        for rule in vue_api.url_map._rules:
            print(f"- {rule.rule} ({', '.join(rule.methods)})")
            
    except Exception as e:
        print(f"❌ Error importing Vue API blueprint: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the health endpoint
    try:
        print("\nTesting health endpoint...")
        response = requests.get("http://localhost:5000/casestrainer/api/health")
        print(f"Status Code: {response.status_code}")
        print("Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print("\nResponse Body:")
        print(json.dumps(response.json(), indent=2))
        
        # Check if this is the debug or Vue API
        if "Debug API" in response.text:
            print("\n⚠️  WARNING: Debug API is active instead of Vue API")
            print("This should not happen in production!")
        else:
            print("\n✅ Vue API is working correctly")
            
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vue_api_health()
