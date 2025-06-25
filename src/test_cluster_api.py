#!/usr/bin/env python3
"""
Test script for CourtListener Cluster API
"""
import requests
import json
import sys


def test_cluster_api(api_key, cluster_id):
    """Test the CourtListener Cluster API with a specific cluster ID."""
    print(f"Testing CourtListener Cluster API with cluster ID: {cluster_id}")

    # API endpoint
    api_url = f"https://www.courtlistener.com/api/rest/v4/clusters/{cluster_id}/"

    # Prepare the request
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}

    # Make the request
    print(f"Sending request to {api_url}")
    try:
        response = requests.get(api_url, headers=headers)

        # Check the response
        print(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            print("API request successful")
            result = response.json()

            # Save the API response to a file for inspection
            with open("test_cluster_response.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print("API response saved to test_cluster_response.json")

            # Print a summary of the response
            print("\nResponse summary:")
            print(f"Case name: {result.get('case_name', 'N/A')}")
            print(f"Court: {result.get('court_id', 'N/A')}")
            print(f"Date filed: {result.get('date_filed', 'N/A')}")
            print(f"Docket number: {result.get('docket_id', 'N/A')}")

            # Extract citation information
            citations = result.get("citations", [])
            if citations:
                print("\nCitations:")
                for citation in citations:
                    print(
                        f"  {citation.get('volume')} {citation.get('reporter')} {citation.get('page')}"
                    )

            return True
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"Error querying CourtListener API: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Load API key from config.json
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            api_key = config.get("courtlistener_api_key")
            if not api_key:
                print("No CourtListener API key found in config.json")
                sys.exit(1)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        sys.exit(1)

    # Test cluster ID
    cluster_id = "5093516"  # From the previous API response
    if len(sys.argv) > 1:
        cluster_id = sys.argv[1]

    test_cluster_api(api_key, cluster_id)
