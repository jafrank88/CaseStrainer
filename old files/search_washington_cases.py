#!/usr/bin/env python3
"""
Script to search for Washington state cases in CourtListener
"""
import json
import requests
import sys


def search_washington_cases(query="*", num_results=10):
    """Search for Washington state cases in CourtListener."""
    print(f"Searching for Washington state cases with query: {query}")

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

    # Set up headers
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}

    # Search parameters
    params = {
        "q": query,
        "court": "wash washctapp",  # Washington Supreme Court and Court of Appeals
        "order_by": "dateFiled desc",  # Most recent first
        "type": "o",  # Opinions only
        "format": "json",
    }

    # Make the request
    try:
        response = requests.get(
            "https://www.courtlistener.com/api/rest/v3/search/",
            headers=headers,
            params=params,
        )

        if response.status_code == 200:
            results = response.json()

            print(f"Found {results.get('count', 0)} results")

            # Save all results to file
            with open("washington_cases.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            print("Full results saved to washington_cases.json")

            # Extract and print case information
            cases = []
            for i, result in enumerate(results.get("results", [])[:num_results]):
                case = {
                    "id": result.get("id"),
                    "case_name": result.get("caseName", "Unknown"),
                    "court": result.get("court", "Unknown Court"),
                    "date_filed": result.get("dateFiled", "Unknown Date"),
                    "citation": result.get("citation", []),
                    "docket_number": result.get("docketNumber", "Unknown"),
                    "absolute_url": result.get("absolute_url", ""),
                }
                cases.append(case)

                print(f"\nCase {i+1}:")
                print(f"  Name: {case['case_name']}")
                print(f"  Court: {case['court']}")
                print(f"  Date: {case['date_filed']}")
                print(f"  Citation: {case['citation']}")
                print(f"  URL: https://www.courtlistener.com{case['absolute_url']}")

            # Save extracted cases to file
            with open("washington_cases_extracted.json", "w", encoding="utf-8") as f:
                json.dump(cases, f, indent=2)
            print("\nExtracted cases saved to washington_cases_extracted.json")

            return cases
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return []

    except Exception as e:
        print(f"Error searching for cases: {e}")
        import traceback

        traceback.print_exc()
        return []


if __name__ == "__main__":
    # Get query from command line argument or use default
    query = "*"  # Default: all cases
    if len(sys.argv) > 1:
        query = sys.argv[1]

    # Get number of results from command line argument or use default
    num_results = 10  # Default: 10 cases
    if len(sys.argv) > 2:
        num_results = int(sys.argv[2])

    search_washington_cases(query, num_results)
