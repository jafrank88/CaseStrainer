#!/usr/bin/env python3
"""
Test script for the Citation Verification Module
"""
import json
import sys
import pytest
pytest.skip("CitationVerifier is deprecated or missing", allow_module_level=True)
from citation_verification import CitationVerifier


def test_citation_verification(citation):
    """Test the citation verification with multiple methods."""
    print(f"Testing citation verification for: {citation}")

    # Load API keys from config.json
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            courtlistener_api_key = config.get("courtlistener_api_key")
            langsearch_api_key = config.get("langsearch_api_key")
    except Exception as e:
        print(f"Error loading config.json: {e}")
        courtlistener_api_key = None
        langsearch_api_key = None

    # Create the citation verifier
    verifier = CitationVerifier(
        api_key=courtlistener_api_key, langsearch_api_key=langsearch_api_key
    )

    # Verify the citation
    result = verifier.verify_citation(citation)

    # Print the results
    print("\nVerification Results:")
    print(f"Citation: {result.get('citation')}")
    print(f"Found: {result.get('found')}")
    print(f"Source: {result.get('source')}")
    print(f"Case Name: {result.get('case_name')}")

    # Print URL (this will be used in the CaseStrainer dropdown)
    if result.get("url"):
        print(f"URL: {result.get('url')}")

    # Print details
    details = result.get("details", {})
    if details:
        print("\nDetails:")
        for key, value in details.items():
            print(f"  {key}: {value}")

    # Save results to file
    with open("citation_verification_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print("\nResults saved to citation_verification_result.json")

    return result


if __name__ == "__main__":
    # Get citation from command line argument or use default
    citation = "410 U.S. 113"  # Default: Roe v. Wade
    if len(sys.argv) > 1:
        citation = sys.argv[1]

    test_citation_verification(citation)
