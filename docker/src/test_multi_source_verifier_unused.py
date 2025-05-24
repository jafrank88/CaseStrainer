"""
Test script for the multi-source verifier.

This script tests the multi-source verifier with various types of citations
to ensure it correctly distinguishes between real cases, hallucinations, and typos.
"""

import os
import json
import traceback
from multi_source_verifier import MultiSourceVerifier


# Load API keys from config.json
def load_api_keys():
    """Load API keys from config.json."""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        api_keys = {}
        if "COURTLISTENER_API_KEY" in config:
            api_keys["courtlistener"] = config["COURTLISTENER_API_KEY"]
        if "LANGSEARCH_API_KEY" in config:
            api_keys["langsearch"] = config["LANGSEARCH_API_KEY"]

        return api_keys
    except Exception as e:
        print(f"Error loading API keys: {e}")
        return {}


# Test citations
TEST_CITATIONS = [
    # Landmark cases (should be confirmed)
    {
        "citation": "347 U.S. 483",
        "case_name": "Brown v. Board of Education",
        "expected": "confirmed",
    },
    {"citation": "410 U.S. 113", "case_name": "Roe v. Wade", "expected": "confirmed"},
    {
        "citation": "384 U.S. 436",
        "case_name": "Miranda v. Arizona",
        "expected": "confirmed",
    },
    # Valid citations but might not be in databases
    {"citation": "123 F.3d 456", "case_name": "Smith v. Jones", "expected": "unknown"},
    {
        "citation": "456 F.Supp.2d 789",
        "case_name": "Johnson v. Department of Justice",
        "expected": "unknown",
    },
    {
        "citation": "789 F.2d 123",
        "case_name": "Williams v. City of Seattle",
        "expected": "unknown",
    },
    # Invalid format (hallucinations)
    {
        "citation": "963 F.4th 578",
        "case_name": "Williams v. State of Washington",
        "expected": "hallucination",
    },
    {
        "citation": "972 Wash. 402",
        "case_name": "Davis v. City of Seattle",
        "expected": "hallucination",
    },
    # Invalid volume (typos)
    {
        "citation": "722 U.S. 866",
        "case_name": "Smith v. Department of Justice",
        "expected": "typo",
    },
    {
        "citation": "270 S. Ct. 205",
        "case_name": "Johnson v. United States",
        "expected": "typo",
    },
    # Westlaw citations (might be real)
    {
        "citation": "2019 WL 6686274",
        "case_name": "Martinez v. Department of Corrections",
        "expected": "unknown",
    },
    {
        "citation": "2020 WL 1234567",
        "case_name": "Garcia v. State of California",
        "expected": "unknown",
    },
]


def test_verifier():
    """Test the multi-source verifier with various citations."""
    # Load API keys
    api_keys = load_api_keys()

    # Create verifier
    verifier = MultiSourceVerifier(api_keys)

    # Results summary
    results = {
        "total": len(TEST_CITATIONS),
        "confirmed": 0,
        "unconfirmed": 0,
        "format_errors": 0,
        "volume_errors": 0,
        "details": [],
    }

    # Test each citation
    for test in TEST_CITATIONS:
        print(f"\nVerifying: {test['citation']} ({test['case_name']})")
        print(f"Expected: {test['expected']}")

        try:
            # Verify citation
            result = verifier.verify_citation(test["citation"], test["case_name"])

            # Print result
            print(f"Found: {result['found']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Explanation: {result['explanation']}")
            print(f"Source: {result['source']}")

            # Update results summary
            if result["found"]:
                results["confirmed"] += 1
            else:
                results["unconfirmed"] += 1

                # Check for format errors
                if "format_analysis" in result and not result["format_analysis"].get(
                    "is_valid_format", True
                ):
                    results["format_errors"] += 1

                # Check for volume errors
                if "format_analysis" in result and not result["format_analysis"].get(
                    "is_valid_volume", True
                ):
                    results["volume_errors"] += 1

            # Add to details
            results["details"].append(
                {
                    "citation": test["citation"],
                    "case_name": test["case_name"],
                    "expected": test["expected"],
                    "found": result["found"],
                    "confidence": result["confidence"],
                    "explanation": result["explanation"],
                    "source": result["source"],
                }
            )

        except Exception as e:
            print(f"Error verifying citation: {e}")
            traceback.print_exc()

            # Add error to details
            results["details"].append(
                {
                    "citation": test["citation"],
                    "case_name": test["case_name"],
                    "expected": test["expected"],
                    "error": str(e),
                }
            )

            results["unconfirmed"] += 1

        print("-" * 50)

    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Total citations: {results['total']}")
    print(
        f"Confirmed: {results['confirmed']} ({results['confirmed']/results['total']*100:.1f}%)"
    )
    print(
        f"Unconfirmed: {results['unconfirmed']} ({results['unconfirmed']/results['total']*100:.1f}%)"
    )
    print(
        f"Format errors: {results['format_errors']} ({results['format_errors']/results['total']*100:.1f}%)"
    )
    print(
        f"Volume errors: {results['volume_errors']} ({results['volume_errors']/results['total']*100:.1f}%)"
    )

    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to test_results.json")

    return results


if __name__ == "__main__":
    test_verifier()
