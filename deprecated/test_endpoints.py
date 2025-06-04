import requests
import json


def test_endpoint(method, url, **kwargs):
    print(f"\nTesting {method} {url}")
    print("-" * 50)
    try:
        response = requests.request(method, url, timeout=10, **kwargs)
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:", json.dumps(response.json(), indent=2))
        except ValueError:
            print("Response (non-JSON):", response.text[:500])
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None


# Test root endpoint
print("Testing API Endpoints")
print("=" * 50)

test_endpoint("GET", "http://localhost:5000/")

test_endpoint("GET", "http://localhost:5000/casestrainer/")

# Test citation verification
test_endpoint(
    "POST",
    "http://localhost:5000/casestrainer/api/verify_citation",
    json={"citation": "347 U.S. 483"},
)

# Test text analysis
test_endpoint(
    "POST",
    "http://localhost:5000/casestrainer/api/text",
    json={
        "text": "In Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court ruled that segregation was unconstitutional."
    },
)

print("\nAll tests completed")
