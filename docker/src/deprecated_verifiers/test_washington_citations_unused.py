#!/usr/bin/env python3
"""
Script to test citation verification on Washington state cases
"""
import json
import time
import re
from citation_verification import CitationVerifier


def extract_citations_from_cases():
    """Extract citations from the previously saved Washington cases."""
    try:
        # Load the cases
        with open("washington_cases_extracted.json", "r", encoding="utf-8") as f:
            cases = json.load(f)

        print(f"Loaded {len(cases)} cases")

        # Extract citations
        citations = []
        for case in cases:
            # Try to extract citation from the citation field
            case_citation = case.get("citation")
            if case_citation and case_citation != "None":
                citations.append(
                    {
                        "citation": case_citation,
                        "case_name": case.get("case_name"),
                        "court": case.get("court"),
                        "date_filed": case.get("date_filed"),
                        "source": "citation field",
                    }
                )
                continue

            # If no citation in citation field, try to extract from case name
            case_name = case.get("case_name", "")
            citation_match = re.search(
                r"(\d+\s+Wash\.\s+(?:2d|App\.)?\s+\d+)", case_name
            )
            if citation_match:
                citations.append(
                    {
                        "citation": citation_match.group(1),
                        "case_name": case.get("case_name"),
                        "court": case.get("court"),
                        "date_filed": case.get("date_filed"),
                        "source": "case name",
                    }
                )
                continue

            # If still no citation, try to get it from the URL
            url = case.get("absolute_url", "")
            if url:
                # Make a request to get the opinion page
                import requests

                try:
                    response = requests.get(f"https://www.courtlistener.com{url}")
                    if response.status_code == 200:
                        # Look for citation in the page content
                        citation_match = re.search(
                            r"(\d+\s+Wash\.\s+(?:2d|App\.)?\s+\d+)", response.text
                        )
                        if citation_match:
                            citations.append(
                                {
                                    "citation": citation_match.group(1),
                                    "case_name": case.get("case_name"),
                                    "court": case.get("court"),
                                    "date_filed": case.get("date_filed"),
                                    "source": "opinion page",
                                }
                            )
                            continue
                except Exception as e:
                    print(f"Error fetching opinion page: {e}")

            # If we still don't have a citation, add the case without one
            citations.append(
                {
                    "citation": None,
                    "case_name": case.get("case_name"),
                    "court": case.get("court"),
                    "date_filed": case.get("date_filed"),
                    "source": "no citation found",
                }
            )

        # Save the extracted citations
        with open("washington_citations.json", "w", encoding="utf-8") as f:
            json.dump(citations, f, indent=2)

        print(
            f"Extracted {len(citations)} citations and saved to washington_citations.json"
        )
        return citations

    except Exception as e:
        print(f"Error extracting citations: {e}")
        import traceback

        traceback.print_exc()
        return []


def test_citation_verification(citations):
    """Test the citation verification system on the extracted citations."""
    print("\nTesting citation verification...")

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

    # Test each citation
    results = []
    for i, citation_info in enumerate(citations):
        citation = citation_info.get("citation")
        if not citation:
            print(
                f"\nSkipping case {i+1}: {citation_info.get('case_name')} - No citation found"
            )
            results.append(
                {
                    "citation": None,
                    "case_name": citation_info.get("case_name"),
                    "found": False,
                    "source": None,
                    "verification_result": None,
                }
            )
            continue

        print(f"\nTesting case {i+1}: {citation_info.get('case_name')}")
        print(f"Citation: {citation}")

        # Verify the citation
        result = verifier.verify_citation(citation)

        # Print the results
        print(f"Found: {result.get('found')}")
        print(f"Source: {result.get('source')}")
        print(f"Verified Case Name: {result.get('case_name')}")

        # Add to results
        results.append(
            {
                "citation": citation,
                "case_name": citation_info.get("case_name"),
                "found": result.get("found"),
                "source": result.get("source"),
                "verification_result": result,
            }
        )

        # Sleep to avoid rate limiting
        time.sleep(1)

    # Save the verification results
    with open("citation_verification_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\nVerification results saved to citation_verification_results.json")

    # Count successes and failures
    successes = sum(1 for r in results if r.get("found"))
    failures = sum(1 for r in results if not r.get("found") and r.get("citation"))
    no_citations = sum(1 for r in results if not r.get("citation"))

    print("\nSummary:")
    print(f"  Total cases: {len(results)}")
    print(f"  Successfully verified: {successes}")
    print(f"  Failed to verify: {failures}")
    print(f"  No citation found: {no_citations}")

    # List cases that couldn't be verified
    if failures > 0:
        print("\nCases that couldn't be verified:")
        for r in results:
            if not r.get("found") and r.get("citation"):
                print(f"  - {r.get('case_name')}: {r.get('citation')}")

    return results


if __name__ == "__main__":
    # Extract citations from previously saved cases
    citations = extract_citations_from_cases()

    # Test citation verification
    if citations:
        test_citation_verification(citations)
