"""
Test script to check the backend health check endpoint
"""
import requests
import sys

def test_backend_health():
    """Test the backend health check endpoint"""
    print("=== TESTING BACKEND HEALTH CHECK ===\n")
    
    # Try localhost first (for direct testing)
    urls = [
        "http://localhost:5000/casestrainer/api/health",
        "http://localhost:5001/casestrainer/api/health"
    ]
    
    for url in urls:
        print(f"Testing URL: {url}")
        try:
            response = requests.get(url, timeout=10)
            print(f"  Status Code: {response.status_code}")
            print(f"  Response: {response.text[:200]}...")
            print(f"  Headers: {dict(response.headers)}")
            
            # Check if this is the Vue API or debug API
            if "Vue API" in response.text:
                print("  ✅ Vue API is responding")
            elif "Debug API" in response.text:
                print("  ⚠️  Debug API is responding instead of Vue API")
            else:
                print("  ❓ Unknown API response")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error connecting to {url}: {e}")
        print()

if __name__ == "__main__":
    test_backend_health()
