import requests
import json
import time
import pytest

# Suppress asyncio warning
pytestmark = pytest.mark.filterwarnings(
    "ignore::pytest.PytestUnhandledThreadExceptionWarning"
)

# Base URL for the API
BASE_URL = "http://localhost:5000/casestrainer/api"

# Test data
TEST_TEXT = """
This is a test document containing several legal citations:
1. 171 Wash. 2d 486 - A Washington Supreme Court case
2. 123 F.3d 456 - A federal case
3. 987 F.2d 654 - Another federal case
"""

def test_analyze_text():
    """Test the analyze endpoint with text input"""
    analyze_url = f"{BASE_URL}/analyze"
    
    print("=" * 80)
    print("TESTING ANALYZE ENDPOINT (TEXT INPUT)")
    print("=" * 80)
    print(f"URL: {analyze_url}")
    print("Method: POST")
    print(f"Request data: {{'text': '...<truncated>...'}}")
    print("-" * 80)

    try:
        # Send the analysis request
        print("Sending analysis request...")
        response = requests.post(
            analyze_url,
            json={"text": TEST_TEXT},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # Check if request was successful
        assert response.status_code == 200, \
            f"Expected status 200, got {response.status_code}"
        
        response_data = response.json()
        print(f"Analysis completed. Status: {response_data.get('status')}")
        
        # Check if we have results
        if 'results' in response_data:
            results = response_data['results']
            print(f"\nFound {len(results)} citations:")
            for i, citation in enumerate(results, 1):
                print(f"{i}. {citation.get('citation', 'N/A')} - {citation.get('case_name', 'N/A')}")
        
        return response_data

    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON response: {e}")
        if 'response' in locals():
            print(f"Response content: {response.text}")
        print(f"\nERROR: Failed to decode JSON: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            try:
                print(f"Response body: {e.response.json()}")
            except:
                print(f"Response text: {e.response.text}")
        raise
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise

    print("=" * 80)


if __name__ == "__main__":
    test_analyze_text()
