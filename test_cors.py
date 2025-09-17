import requests

def test_cors(origin):
    url = "https://wolf.law.uw.edu/casestrainer/api/health"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type"
    }
    
    print(f"\nTesting origin: {origin}")
    
    # Test OPTIONS (preflight) request
    try:
        response = requests.options(url, headers=headers, timeout=5)
        print(f"OPTIONS Status: {response.status_code}")
        print("Response Headers:")
        for k, v in response.headers.items():
            if k.lower().startswith('access-control'):
                print(f"  {k}: {v}")
    except Exception as e:
        print(f"OPTIONS Error: {e}")
    
    # Test GET request
    try:
        response = requests.get(url, headers={"Origin": origin}, timeout=5)
        print(f"\nGET Status: {response.status_code}")
        print("Response Headers:")
        for k, v in response.headers.items():
            if k.lower().startswith('access-control'):
                print(f"  {k}: {v}")
    except Exception as e:
        print(f"GET Error: {e}")

# Test allowed origins
print("=== Testing Allowed Origins ===")
test_cors("https://wolf.law.uw.edu")
test_cors("http://localhost:8080")
test_cors("https://case.law.uw.edu")

# Test disallowed origin
print("\n=== Testing Disallowed Origin ===")
test_cors("https://malicious-site.com")
