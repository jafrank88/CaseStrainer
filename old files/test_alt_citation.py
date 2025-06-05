#!/usr/bin/env python

import json
import requests

# Load API key from config.json
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        API_KEY = config.get("courtlistener_api_key", "")
        print(f"Loaded API key: {API_KEY[:5]}...")
except Exception as e:
    print(f"Error loading config.json: {e}")
    API_KEY = input("Enter your CourtListener API key: ")

# CourtListener API URL
COURTLISTENER_API_URL = "https://www.courtlistener.com/api/rest/v3/citation-lookup/"


def query_courtlistener_api(citation, api_key):
    """Query the CourtListener API to verify a single citation."""
    print(f"Querying CourtListener API with citation: {citation}")

    if not api_key:
        print("No API key provided")
        return {"error": "No API key provided"}

    try:
        # Prepare the request
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }

        # Prepare the data with just the citation
        data = {"text": citation}

        # Make the request
        print(f"Sending request to {COURTLISTENER_API_URL}")
        response = requests.post(COURTLISTENER_API_URL, headers=headers, json=data)

        # Check the response
        if response.status_code == 200:
            print("API request successful")
            result = response.json()

            # Save the API response to a file for inspection
            try:
                with open("api_alt_response.json", "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                print("API response saved to api_alt_response.json")
            except Exception as e:
                print(f"Error saving API response to file: {e}")

            return result
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return {
                "error": f"API request failed with status code {response.status_code}: {response.text}"
            }

    except Exception as e:
        print(f"Error querying CourtListener API: {e}")
        import traceback

        traceback.print_exc()
        return {"error": f"Error querying CourtListener API: {str(e)}"}


def main():
    # Test alternative citation for Bell Atlantic Corp. v. Twombly
    test_citation = "127 S.Ct. 1955"

    print(f"Testing alternative citation: {test_citation}")

    # Query the API
    result = query_courtlistener_api(test_citation, API_KEY)

    # Print the result
    print("\nAPI Response:")
    print(json.dumps(result, indent=2))

    # Extract specific information if available
    if isinstance(result, list):
        for item in result:
            if "citation" in item:
                print(f"\nCitation: {item['citation']}")
                if "normalized_citations" in item:
                    print(f"Normalized Citations: {item['normalized_citations']}")
                if "clusters" in item and item["clusters"]:
                    cluster = item["clusters"][0]
                    print(f"Case Name: {cluster.get('case_name', 'Unknown')}")
                    print(f"URL: {cluster.get('absolute_url', 'Unknown')}")
                    if "citations" in cluster:
                        print("\nAll Citations for this case:")
                        for citation in cluster["citations"]:
                            print(
                                f"  {citation.get('reporter', '')}: {citation.get('volume', '')}-{citation.get('page', '')}"
                            )


if __name__ == "__main__":
    main()
