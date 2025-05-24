"""
Test script to check if previously unverified citations can now be verified
using the multi-source verification system.
"""

import json
import sys
import os
import traceback
from multi_source_verifier import MultiSourceVerifier

# Sample of previously unverified citations
UNVERIFIED_CITATIONS = [
    # Common unverified citations from previous runs
    "410 U.S. 113 (1973)",  # Roe v. Wade - should be verifiable
    "347 U.S. 483 (1954)",  # Brown v. Board of Education - should be verifiable
    "384 U.S. 436 (1966)",  # Miranda v. Arizona - should be verifiable
    "123 F.3d 456 (9th Cir. 1997)",  # Made-up citation
    "567 U.S. 890 (2012)",  # Made-up citation
    "789 F.2d 123 (2d Cir. 1985)",  # Made-up citation
    "456 F. Supp. 2d 789 (S.D.N.Y. 2005)",  # Made-up citation
    "123 Cal. App. 4th 456 (2004)",  # Made-up citation
    "456 N.E.2d 789 (N.Y. 1983)",  # Made-up citation
    "789 P.3d 123 (Colo. 2020)",  # Made-up citation
    # Citations with typos
    "576 U.S. 644 (2015)",  # Obergefell v. Hodges - correct
    "576 U.S. 645 (2015)",  # Typo in page number
    "577 U.S. 644 (2015)",  # Typo in volume
    "576 U.S. 644 (2016)",  # Typo in year
    # Citations with formatting issues
    "576US644(2015)",  # No spaces
    "576 U. S. 644 (2015)",  # Extra spaces
    "U.S. 576, 644 (2015)",  # Reversed format
]


def test_citations():
    """Test all unverified citations with the multi-source verifier."""
    print("Testing previously unverified citations with multi-source verifier...")

    # Initialize the verifier
    verifier = MultiSourceVerifier()

    results = {"verified_count": 0, "unverified_count": 0, "results": []}

    for citation in UNVERIFIED_CITATIONS:
        print(f"\nTesting citation: {citation}")
        try:
            # Verify the citation
            result = verifier.verify_citation(citation)

            # Add to results
            status = "VERIFIED" if result.get("found", False) else "UNVERIFIED"
            confidence = result.get("confidence", 0)
            explanation = result.get("explanation", "No explanation provided")

            print(f"Status: {status}")
            print(f"Confidence: {confidence}")
            print(f"Explanation: {explanation}")

            if result.get("found", False):
                results["verified_count"] += 1
            else:
                results["unverified_count"] += 1

            results["results"].append(
                {
                    "citation": citation,
                    "status": status,
                    "confidence": confidence,
                    "explanation": explanation,
                    "source": result.get("source", "Unknown"),
                    "details": result,
                }
            )

        except Exception as e:
            print(f"Error verifying citation {citation}: {e}")
            traceback.print_exc()
            results["results"].append(
                {"citation": citation, "status": "ERROR", "explanation": str(e)}
            )

    # Save results to file
    with open("unverified_citations_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n\n===== SUMMARY =====")
    print(f"Total citations tested: {len(UNVERIFIED_CITATIONS)}")
    print(f"Citations now verified: {results['verified_count']}")
    print(f"Citations still unverified: {results['unverified_count']}")
    print(
        f"Success rate: {results['verified_count'] / len(UNVERIFIED_CITATIONS) * 100:.2f}%"
    )
    print("Full results saved to unverified_citations_test_results.json")

    return results


if __name__ == "__main__":
    test_citations()
