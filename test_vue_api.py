"""
Test script to verify Vue API endpoint
"""
import sys
import os
import json
import requests

# Test the Vue API health endpoint
try:
    print("=== TESTING VUE API HEALTH ENDPOINT ===")
    response = requests.get("http://localhost:5000/casestrainer/api/health")
    print(f"Status Code: {response.status_code}")
    print("Response Headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")
    print("\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
    
    # Check if this is the debug or production API
    data = response.json()
    if "Debug API" in data.get("message", ""):
        print("\n⚠️  WARNING: Debug API is active instead of Vue API")
        print("This should not happen in production!")
    else:
        print("\n✅ Vue API is working correctly")
        
except Exception as e:
    print(f"❌ Error testing Vue API: {e}")
    import traceback
    traceback.print_exc()
