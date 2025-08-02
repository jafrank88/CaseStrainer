"""
Script to check registered routes in the running Flask application
"""
import requests

def check_routes():
    """Check registered routes in the running Flask application"""
    print("=== CHECKING REGISTERED ROUTES IN RUNNING APPLICATION ===\n")
    
    # Get the list of routes from the application
    try:
        print("1. Fetching routes from the application...")
        response = requests.get("http://localhost:5000/casestrainer/api/routes")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.headers.get('content-type')}")
        print("\nResponse Body:")
        print(response.text)
        
        # Check if this is the debug API or Vue API
        if "Debug API" in response.text:
            print("\n⚠️  WARNING: Debug API is responding to /casestrainer/api/routes")
        else:
            print("\n✅ Vue API is responding to /casestrainer/api/routes")
        
    except Exception as e:
        print(f"\n❌ Error fetching routes: {e}")
    
    # Check the health endpoint
    try:
        print("\n2. Testing health endpoint...")
        response = requests.get("http://localhost:5000/casestrainer/api/health")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Type: {response.headers.get('content-type')}")
        print("\nResponse Body:")
        print(response.text)
        
        # Check if this is the debug API or Vue API
        if "Debug API" in response.text:
            print("\n⚠️  WARNING: Debug API is responding to /casestrainer/api/health")
        else:
            print("\n✅ Vue API is responding to /casestrainer/api/health")
        
    except Exception as e:
        print(f"\n❌ Error testing health endpoint: {e}")

if __name__ == "__main__":
    check_routes()
