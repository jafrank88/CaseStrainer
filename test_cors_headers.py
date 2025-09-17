import requests
from urllib.parse import urlparse

def test_cors(url, origin):
    """Test CORS headers for a given URL and origin."""
    print(f"\n{'='*80}")
    print(f"Testing CORS for URL: {url}")
    print(f"Origin: {origin}")
    print("-" * 80)
    
    # Prepare headers for OPTIONS request (preflight)
    headers = {
        'Origin': origin,
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type, Authorization',
    }
    
    # Test OPTIONS request (preflight)
    print("\n1. Testing OPTIONS request (preflight):")
    try:
        response = requests.options(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code} {response.reason}")
        print("Response Headers:")
        for key, value in response.headers.items():
            if key.lower().startswith('access-control-'):
                print(f"  {key}: {value}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test GET request
    print("\n2. Testing GET request:")
    try:
        response = requests.get(
            url, 
            headers={'Origin': origin},
            timeout=10
        )
        print(f"Status: {response.status_code} {response.reason}")
        print("Response Headers:")
        for key, value in response.headers.items():
            if key.lower().startswith('access-control-'):
                print(f"  {key}: {value}")
        
        try:
            print("\nResponse Body:")
            print(response.json())
        except:
            print("\nResponse Body (not JSON):")
            print(response.text[:500])  # Print first 500 chars if not JSON
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    base_url = "https://wolf.law.uw.edu/casestrainer/api/health"
    
    # Test with allowed origins
    print("\n" + "="*80)
    print("TESTING ALLOWED ORIGINS")
    print("="*80)
    
    allowed_origins = [
        "https://wolf.law.uw.edu",
        "http://localhost:8080",
        "https://case.law.uw.edu"
    ]
    
    for origin in allowed_origins:
        test_cors(base_url, origin)
    
    # Test with disallowed origin
    print("\n" + "="*80)
    print("TESTING DISALLOWED ORIGIN")
    print("="*80)
    test_cors(base_url, "https://malicious-site.com")
    
    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)
