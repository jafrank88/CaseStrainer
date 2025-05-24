"""
Simple script to test citation verification with our landmark cases database.
"""

import json
import sys
import os
import re

# Import the landmark cases database
try:
    from landmark_cases import LANDMARK_CASES

    print(f"Loaded landmark cases database with {len(LANDMARK_CASES)} cases")
except ImportError:
    print("Warning: landmark_cases module not found.")
    LANDMARK_CASES = {}


def normalize_citation(citation_text):
    """Normalize citation format for matching."""
    # Remove extra whitespace
    citation = re.sub(r"\s+", " ", citation_text.strip())

    # Handle U.S. Reports citations (like "410 U.S. 113")
    us_match = re.match(r"(\d+)\s+U\.?\s?S\.?\s+(\d+)", citation)
    if us_match:
        volume, page = us_match.groups()
        return f"{volume} U.S. {page}"

    return citation


def is_landmark_case(citation_text):
    """Check if a citation corresponds to a landmark case."""
    normalized_citation = normalize_citation(citation_text)

    # Direct lookup
    if normalized_citation in LANDMARK_CASES:
        return LANDMARK_CASES[normalized_citation]

    # Try alternative formats
    for citation, info in LANDMARK_CASES.items():
        # For U.S. Reports citations, check if volume and page match
        us_match1 = re.match(r"(\d+)\s+U\.?\s?S\.?\s+(\d+)", normalized_citation)
        us_match2 = re.match(r"(\d+)\s+U\.?\s?S\.?\s+(\d+)", citation)

        if us_match1 and us_match2:
            vol1, page1 = us_match1.groups()
            vol2, page2 = us_match2.groups()
            if vol1 == vol2 and page1 == page2:
                return info

    return None


def load_unconfirmed_citations(
    filename="downloaded_briefs/all_unconfirmed_citations.json",
):
    """Load unconfirmed citations from the JSON file."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading unconfirmed citations: {e}")
        return {}


def test_against_landmark_cases(citations_to_test=None):
    """Test unconfirmed citations against our landmark cases database."""
    all_citations = load_unconfirmed_citations()

    # Flatten the citations list
    flat_citations = []
    for document, citations in all_citations.items():
        for citation in citations:
            citation["document"] = document
            flat_citations.append(citation)

    # If specific citations are provided, use those
    if citations_to_test:
        test_citations = [
            c for c in flat_citations if c["citation_text"] in citations_to_test
        ]
    else:
        test_citations = flat_citations

    print(
        f"Testing {len(test_citations)} unconfirmed citations against landmark cases database..."
    )

    results = {
        "newly_confirmed": [],
        "still_unconfirmed": [],
        "summary": {
            "total_tested": len(test_citations),
            "newly_confirmed_count": 0,
            "still_unconfirmed_count": 0,
        },
    }

    for citation in test_citations:
        citation_text = citation["citation_text"]
        case_name = citation.get("case_name")
        document = citation.get("document")

        print(f"\nTesting citation: {citation_text} ({case_name}) from {document}")

        # Check if it's a landmark case
        landmark_info = is_landmark_case(citation_text)
        if landmark_info:
            print(
                f"CONFIRMED: Found landmark case: {landmark_info['name']} ({citation_text})"
            )
            citation["verification_result"] = {
                "found": True,
                "found_case_name": landmark_info["name"],
                "confidence": 0.95,
                "explanation": f"Verified landmark case: {landmark_info['name']} ({landmark_info['year']}) - {landmark_info['significance']}",
                "source": "Landmark Cases Database",
            }
            results["newly_confirmed"].append(citation)
            results["summary"]["newly_confirmed_count"] += 1
        else:
            print(
                f"UNCONFIRMED: Citation not found in landmark cases database: {citation_text}"
            )
            results["still_unconfirmed"].append(citation)
            results["summary"]["still_unconfirmed_count"] += 1

    # Calculate percentage of newly confirmed citations
    total = results["summary"]["total_tested"]
    newly_confirmed = results["summary"]["newly_confirmed_count"]
    percentage = (newly_confirmed / total) * 100 if total > 0 else 0
    results["summary"]["percentage_confirmed"] = round(percentage, 2)

    return results


def save_results(results, filename="landmark_verification_results.json"):
    """Save the verification results to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {filename}")
    except Exception as e:
        print(f"Error saving results: {e}")


def test_landmark_cases():
    """Test known landmark cases to verify they are correctly identified."""
    landmark_test_cases = [
        "410 U.S. 113",  # Roe v. Wade
        "347 U.S. 483",  # Brown v. Board of Education
        "376 U.S. 254",  # New York Times v. Sullivan
        "384 U.S. 436",  # Miranda v. Arizona
        "5 U.S. 137",  # Marbury v. Madison
        "198 U.S. 45",  # Lochner v. New York
        "163 U.S. 537",  # Plessy v. Ferguson
        "531 U.S. 98",  # Bush v. Gore
    ]

    print("\n===== TESTING LANDMARK CASES =====\n")
    confirmed_count = 0

    for citation in landmark_test_cases:
        print(f"Testing landmark citation: {citation}")
        landmark_info = is_landmark_case(citation)

        if landmark_info:
            print(f"✓ CONFIRMED: {landmark_info['name']} ({landmark_info['year']})")
            print(f"  Significance: {landmark_info['significance']}")
            confirmed_count += 1
        else:
            print(f"✗ NOT FOUND IN DATABASE: {citation}")

    print(
        f"\nLandmark cases confirmed: {confirmed_count}/{len(landmark_test_cases)} ({confirmed_count/len(landmark_test_cases)*100:.1f}%)"
    )


def main():
    # First test landmark cases
    test_landmark_cases()

    # Then test unconfirmed citations
    test_citations = [
        # Unconfirmed citations from our database (to check if any are actually landmark cases)
        "175 F.3d 257",
        "57 F.Supp.2d 460",
        "928 F.2d 739",
        "605 F.3d 144",
        "334 F.Supp.3d 335",
        "722 U.S. 866",
        "270 S. Ct. 205",
        "833 F.2d 882",
        "671 Wash.2d 228",
        "760 F.4th 44",
        "672 Wash. 60",
        "367 F.Supp.3d 797",
        "963 F.4th 578",
    ]

    results = test_against_landmark_cases(test_citations)

    # Print summary
    print("\n===== VERIFICATION RESULTS =====")
    print(f"Total citations tested: {results['summary']['total_tested']}")
    print(
        f"Newly confirmed citations: {results['summary']['newly_confirmed_count']} ({results['summary']['percentage_confirmed']}%)"
    )
    print(
        f"Still unconfirmed citations: {results['summary']['still_unconfirmed_count']}"
    )

    # Print details of newly confirmed citations
    if results["newly_confirmed"]:
        print("\nNEWLY CONFIRMED CITATIONS:")
        for i, citation in enumerate(results["newly_confirmed"], 1):
            result = citation["verification_result"]
            print(
                f"{i}. {citation['citation_text']} ({citation.get('case_name', 'N/A')})"
            )
            print(f"   Confidence: {result.get('confidence', 0) * 100:.1f}%")
            print(f"   Source: {result.get('source', 'Unknown')}")
            print(
                f"   Explanation: {result.get('explanation', 'No explanation provided')}"
            )
            print()

    # Save the results
    save_results(results)


if __name__ == "__main__":
    main()
