import requests
import json


def test_api_endpoint(url, method="GET", data=None, headers=None):
    """Test an API endpoint and return the response."""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        else:
            return {"error": f"Unsupported HTTP method: {method}"}

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content": response.text[:1000],  # Return first 1000 chars of response
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    base_url = "http://localhost:5000/casestrainer/api"

    # Test GET /version
    print("\nTesting GET /version:")
    result = test_api_endpoint(f"{base_url}/version")
    print(json.dumps(result, indent=2))

    # Test POST /analyze with sample text
    print("\nTesting POST /analyze with sample text:")
    test_data = {"text": "This is a test with citation 534 F.3d 1290"}
    result = test_api_endpoint(
        f"{base_url}/analyze",
        method="POST",
        data=test_data,
        headers={"Content-Type": "application/json"},
    )
    print(json.dumps(result, indent=2))

    # List available endpoints
    print("\nAvailable API endpoints:")
    print(f"  GET    {base_url}/version")
    print(f"  POST   {base_url}/analyze")
    print(f"  GET    {base_url}/confirmed_with_multitool_data")
    print(f"  GET    {base_url}/processing_progress")
    print(f"  POST   {base_url}/validate_citations")


if __name__ == "__main__":
    main()
