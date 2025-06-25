#!/usr/bin/env python3
"""
Comprehensive Test Suite for CourtListener API Integration
This script combines tests for different CourtListener API endpoints into a single testbed.
It includes tests for Opinion API, Citation Lookup API, and Cluster API.
"""

import requests
import json
import sys
import traceback
import time

def test_opinion_api(api_key, opinion_id="4910901"):
    """Test the CourtListener Opinion API with a specific opinion ID."""
    print(f"Testing CourtListener Opinion API with opinion ID: {opinion_id}")

    # API endpoint
    api_url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"

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
            with open("test_opinion_response.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print("API response saved to test_opinion_response.json")

            # Print a summary of the response
            print("\nResponse summary:")
            print(f"Case name: {result.get('case_name', 'N/A')}")
            print(f"Citation: {result.get('citation', 'N/A')}")
            print(f"Court: {result.get('court', 'N/A')}")
            print(f"Date filed: {result.get('date_filed', 'N/A')}")

            # Extract citation information
            cluster = result.get("cluster", {})
            if isinstance(cluster, dict):
                print("\nCitations:")
                citations = cluster.get("citations", [])
                for citation in citations:
                    print(
                        f"  {citation.get('volume')} {citation.get('reporter')} {citation.get('page')}"
                    )
            elif cluster:
                print(f"\nCluster reference: {cluster}")

            return True
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"Error querying CourtListener Opinion API: {e}")
        traceback.print_exc()
        return False

def test_citation_lookup(api_key, citation="410 U.S. 113"):
    """Test the CourtListener API with a single citation."""
    print(f"Testing CourtListener Citation Lookup API with citation: {citation}")

    # API endpoint
    api_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"

    # Prepare the request
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}

    data = {"text": citation}

    # Make the request
    print(f"Sending request to {api_url}")
    try:
        response = requests.post(api_url, headers=headers, json=data)

        # Check the response
        print(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            print("API request successful")
            result = response.json()

            # Save the API response to a file for inspection
            with open("test_citation_response.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print("API response saved to test_citation_response.json")

            # Print a summary of the response
            print("\nResponse summary:")
            if isinstance(result, list):
                for item in result:
                    print(f"Citation: {item.get('citation', 'N/A')}")
                    clusters = item.get("clusters", [])
                    if clusters:
                        cluster = clusters[0]
                        print(f"Case name: {cluster.get('case_name', 'N/A')}")
                        print(f"Court: {cluster.get('court', 'N/A')}")
                        print(f"Date filed: {cluster.get('date_filed', 'N/A')}")
                        print(f"URL: {cluster.get('absolute_url', 'N/A')}")
                        print("Citations:")
                        for cite in cluster.get("citations", []):
                            print(
                                f"  {cite.get('volume')} {cite.get('reporter')} {cite.get('page')}"
                            )
                    else:
                        print("No case details found")
                    print()
            elif "citations" in result:
                for citation in result["citations"]:
                    print(f"Citation: {citation.get('citation', 'N/A')}")
                    print(f"Found: {citation.get('found', False)}")
                    if citation.get("found"):
                        print(f"Case name: {citation.get('case_name', 'N/A')}")
                        print(f"Court: {citation.get('court', 'N/A')}")
                        print(f"Year: {citation.get('year', 'N/A')}")
                    print()
            else:
                print("No citations found in the response")

            return True
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"Error querying CourtListener Citation Lookup API: {e}")
        traceback.print_exc()
        return False

def test_cluster_api(api_key, cluster_id="5093516"):
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
        print(f"Error querying CourtListener Cluster API: {e}")
        traceback.print_exc()
        return False

def test_opinion_api_invalid_id(api_key, opinion_id="invalid_id"):
    """Test the CourtListener Opinion API with an invalid opinion ID."""
    print(f"Testing CourtListener Opinion API with invalid opinion ID: {opinion_id}")

    # API endpoint
    api_url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"

    # Prepare the request
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}

    # Make the request
    print(f"Sending request to {api_url}")
    try:
        response = requests.get(api_url, headers=headers)

        # Check the response
        print(f"Response status code: {response.status_code}")

        if response.status_code != 200:
            print("Expected failure for invalid ID received")
            print(f"Response: {response.text[:200]}...")
            return True
        else:
            print("Unexpected success for invalid ID")
            return False

    except Exception as e:
        print(f"Error querying CourtListener Opinion API: {e}")
        traceback.print_exc()
        return False

def test_citation_lookup_invalid(api_key, citation="Invalid Citation 123"):
    """Test the CourtListener Citation Lookup API with an invalid citation."""
    print(f"Testing CourtListener Citation Lookup API with invalid citation: {citation}")

    # API endpoint
    api_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"

    # Prepare the request
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}

    data = {"text": citation}

    # Make the request
    print(f"Sending request to {api_url}")
    try:
        response = requests.post(api_url, headers=headers, json=data)

        # Check the response
        print(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            print("API request successful but checking for empty or no results")
            result = response.json()
            
            # Save the API response to a file for inspection
            with open("test_invalid_citation_response.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print("API response saved to test_invalid_citation_response.json")
            
            if isinstance(result, list) and not result:
                print("Empty result list as expected for invalid citation")
                return True
            elif "citations" in result and not any(c.get("found", False) for c in result["citations"]):
                print("No citations found as expected")
                return True
            else:
                print("Unexpected results found for invalid citation")
                return False
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return True  # Failure is expected for invalid citation

    except Exception as e:
        print(f"Error querying CourtListener Citation Lookup API: {e}")
        traceback.print_exc()
        return False

def test_cluster_api_invalid_id(api_key, cluster_id="invalid_id"):
    """Test the CourtListener Cluster API with an invalid cluster ID."""
    print(f"Testing CourtListener Cluster API with invalid cluster ID: {cluster_id}")

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

        if response.status_code != 200:
            print("Expected failure for invalid ID received")
            print(f"Response: {response.text[:200]}...")
            return True
        else:
            print("Unexpected success for invalid ID")
            return False

    except Exception as e:
        print(f"Error querying CourtListener Cluster API: {e}")
        traceback.print_exc()
        return False

def run_all_tests(api_key, opinion_id="4910901", citation="410 U.S. 113", cluster_id="5093516"):
    """Run all CourtListener API tests and return the results summary."""
    print("Running comprehensive test suite for CourtListener API\n")
    
    results = {
        "opinion_api": False,
        "citation_lookup": False,
        "cluster_api": False,
        "opinion_api_invalid": False,
        "citation_lookup_invalid": False,
        "cluster_api_invalid": False
    }
    
    # Test Opinion API
    print("=== Starting Opinion API Test ===")
    results["opinion_api"] = test_opinion_api(api_key, opinion_id)
    print("=== Opinion API Test Complete ===\n")
    time.sleep(1)  # Small delay to avoid rate limiting
    
    # Test Citation Lookup API
    print("=== Starting Citation Lookup API Test ===")
    results["citation_lookup"] = test_citation_lookup(api_key, citation)
    print("=== Citation Lookup API Test Complete ===\n")
    time.sleep(1)  # Small delay to avoid rate limiting
    
    # Test Cluster API
    print("=== Starting Cluster API Test ===")
    results["cluster_api"] = test_cluster_api(api_key, cluster_id)
    print("=== Cluster API Test Complete ===\n")
    time.sleep(1)  # Small delay to avoid rate limiting
    
    # Test Opinion API with Invalid ID
    print("=== Starting Opinion API Invalid ID Test ===")
    results["opinion_api_invalid"] = test_opinion_api_invalid_id(api_key)
    print("=== Opinion API Invalid ID Test Complete ===\n")
    time.sleep(1)  # Small delay to avoid rate limiting
    
    # Test Citation Lookup API with Invalid Citation
    print("=== Starting Citation Lookup API Invalid Citation Test ===")
    results["citation_lookup_invalid"] = test_citation_lookup_invalid(api_key)
    print("=== Citation Lookup API Invalid Citation Test Complete ===\n")
    time.sleep(1)  # Small delay to avoid rate limiting
    
    # Test Cluster API with Invalid ID
    print("=== Starting Cluster API Invalid ID Test ===")
    results["cluster_api_invalid"] = test_cluster_api_invalid_id(api_key)
    print("=== Cluster API Invalid ID Test Complete ===\n")
    
    # Summary
    print("=== Test Suite Summary ===")
    for test_name, success in results.items():
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed

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

    # Default test parameters
    opinion_id = "4910901"  # Cutone v. Law
    citation = "410 U.S. 113"  # Roe v. Wade
    cluster_id = "5093516"  # From a previous API response
    
    # Override with command line arguments if provided
    if len(sys.argv) > 1:
        opinion_id = sys.argv[1]
    if len(sys.argv) > 2:
        citation = sys.argv[2]
    if len(sys.argv) > 3:
        cluster_id = sys.argv[3]
    
    # Run all tests
    run_all_tests(api_key, opinion_id, citation, cluster_id)
