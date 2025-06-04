import requests
import json
import sys
import time
from urllib.parse import urljoin

# Base URLs
BASE_URL = "http://localhost:5000"
PREFIXED_BASE_URL = "http://localhost:5000/casestrainer"


def test_endpoint(url, method="GET", data=None, headers=None, timeout=10):
    """Test an endpoint and return the status and response."""
    try:
        headers = headers or {}
        if "Content-Type" not in headers and method.upper() in ["POST", "PUT", "PATCH"]:
            headers["Content-Type"] = "application/json"

        print(f"  Sending {method} request to {url}")
        if data:
            print(
                f"  With data: {json.dumps(data, indent=2) if isinstance(data, dict) else data}"
            )

        start_time = time.time()

        response = requests.request(
            method.upper(),
            url,
            json=data if isinstance(data, dict) else None,
            data=str(data) if not isinstance(data, dict) else None,
            headers=headers,
            timeout=timeout,
        )

        elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds

        try:
            response_data = response.json()
            return response.status_code, response_data, elapsed
        except ValueError:
            return response.status_code, response.text, elapsed

    except requests.exceptions.RequestException as e:
        return None, f"Request failed: {str(e)}", 0
    except Exception as e:
        return None, f"Unexpected error: {str(e)}", 0


def run_tests():
    print("🚀 Starting API endpoint tests...\n")

    # Test cases
    test_cases = [
        # Root endpoint - should serve the Vue.js app
        {
            "url": "/",
            "name": "Root endpoint (Vue.js app)",
            "method": "GET",
            "expected_status": 200,
        },
        # API version endpoint (both prefixed and non-prefixed)
        {
            "url": "/api/version",
            "name": "API Version (non-prefixed)",
            "method": "GET",
            "expected_status": 200,
        },
        {
            "url": "/casestrainer/api/version",
            "name": "API Version (prefixed)",
            "method": "GET",
            "expected_status": 200,
        },
        # Test citation analysis endpoint
        {
            "url": "/api/analyze",
            "name": "Analyze Citation (non-prefixed)",
            "method": "POST",
            "data": {"text": "Roe v. Wade, 410 U.S. 113 (1973)"},
            "expected_status": 200,
        },
        {
            "url": "/casestrainer/api/analyze",
            "name": "Analyze Citation (prefixed)",
            "method": "POST",
            "data": {"text": "Roe v. Wade, 410 U.S. 113 (1973)"},
            "expected_status": 200,
        },
        # Test static file serving
        {
            "url": "/js/app.js",
            "name": "Static JS file",
            "method": "GET",
            "expected_status": 200,
        },
        {
            "url": "/css/app.css",
            "name": "Static CSS file",
            "method": "GET",
            "expected_status": 200,
        },
    ]

    # Run all test cases
    results = {"total": 0, "passed": 0, "failed": 0, "errors": 0}

    for test in test_cases:
        results["total"] += 1
        url = (
            urljoin(BASE_URL, test["url"])
            if test["url"].startswith("/")
            else test["url"]
        )

        print(f"\n🔍 Testing {test['name']}")
        print(f"   {test['method']} {url}")

        status, response, elapsed = test_endpoint(
            url=url,
            method=test.get("method", "GET"),
            data=test.get("data"),
            headers=test.get("headers"),
        )

        # Format the response for display
        if status is None:
            print(f"  ❌ Error: {response}")
            results["errors"] += 1
            test_result = "ERROR"
        else:
            expected_status = test.get("expected_status", 200)
            status_ok = status == expected_status
            status_icon = "✅" if status_ok else "❌"

            print(
                f"  {status_icon} Status: {status} (expected {expected_status}) - {elapsed:.2f}ms"
            )

            if not status_ok:
                print(f"  ❌ Unexpected status code")
                results["failed"] += 1
                test_result = "FAIL"
            else:
                results["passed"] += 1
                test_result = "PASS"

            # Print response (truncated if too long)
            response_str = (
                json.dumps(response, indent=2)
                if isinstance(response, (dict, list))
                else str(response)
            )
            if len(response_str) > 500:
                response_str = response_str[:500] + "... [truncated]"
            print(f"  📄 Response: {response_str}")

        print(f"  {'─' * 60}")

    # Print summary
    print("\n📊 Test Summary:")
    print(f"   Total tests:  {results['total']}")
    print(f"   ✅ Passed:    {results['passed']}")
    print(f"   ❌ Failed:    {results['failed']}")
    print(f"   ⚠️  Errors:    {results['errors']}")

    if results["failed"] == 0 and results["errors"] == 0:
        print("\n🎉 All tests passed successfully!")
    else:
        print(
            f"\n❌ {results['failed'] + results['errors']} test(s) failed or had errors."
        )


if __name__ == "__main__":
    run_tests()
