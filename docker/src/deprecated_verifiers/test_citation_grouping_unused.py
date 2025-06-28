#!/usr/bin/env python3
"""
Test script for the Citation Grouping Module
"""
import json
import sys
from citation_verification import CitationVerifier
from citation_grouping import group_citations


def test_citation_grouping():
    """Test the citation grouping functionality with multiple citations for the same case."""
    print("Testing citation grouping with multiple citations for the same case")

    # Define test citations
    test_citations = [
        {
            "citation": "410 U.S. 113",
            "case_name": "Roe v. Wade",
            "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/",
            "source": "CourtListener Citation API",
            "details": {"court": "Supreme Court of the United States"},
        },
        {
            "citation": "93 S. Ct. 705",
            "case_name": "Roe v. Wade",
            "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/",
            "source": "CourtListener Citation API",
            "details": {"court": "Supreme Court of the United States"},
        },
        {
            "citation": "35 L. Ed. 2d 147",
            "case_name": "Roe v. Wade",
            "url": "https://www.courtlistener.com/opinion/108713/roe-v-wade/",
            "source": "CourtListener Citation API",
            "details": {"court": "Supreme Court of the United States"},
        },
        {
            "citation": "196 Wash. 2d 725",
            "case_name": "Associated Press v. Washington State Legislature",
            "url": "https://www.courtlistener.com/opinion/4688692/associated-press-v-wash-state-legislature/",
            "source": "CourtListener Search API",
            "details": {"court": "Washington Supreme Court"},
        },
        {
            "citation": "455 P.3d 1164",
            "case_name": "Associated Press v. Wash. State Legislature",
            "url": "https://www.courtlistener.com/opinion/4688692/associated-press-v-wash-state-legislature/",
            "source": "CourtListener Search API",
            "details": {"court": "Washington Supreme Court"},
        },
        {
            "citation": "190 Wash. 2d 1",
            "case_name": "WPEA v. Washington State Center for Childhood Deafness",
            "url": "https://www.courtlistener.com/opinion/4505648/wpea-v-washington-state-center-for-childhood-deafness/",
            "source": "CourtListener Search API",
            "details": {"court": "Washington Supreme Court"},
        },
    ]

    # Group citations
    grouped_citations = group_citations(test_citations)

    # Print results
    print("\n" + "=" * 80)
    print(
        f"Grouped {len(test_citations)} citations into {len(grouped_citations)} groups:"
    )
    print("=" * 80)

    for i, group in enumerate(grouped_citations):
        print(f"\nGROUP {i+1}: {group['case_name']}")
        print(f"  Primary Citation: {group['citation']}")
        print(f"  Source: {group['source']}")
        print(f"  URL: {group['url']}")

        if group.get("alternate_citations"):
            print(f"  Alternate Citations ({len(group['alternate_citations'])}):")
            for alt in group["alternate_citations"]:
                print(f"    - {alt['citation']} ({alt['source']})")

    # Save results to file
    with open("grouped_citations.json", "w", encoding="utf-8") as f:
        json.dump(grouped_citations, f, indent=2)
    print("\nResults saved to grouped_citations.json")

    return grouped_citations


def test_with_real_citations():
    """Test the citation grouping with real citations from the API."""
    print("\nTesting citation grouping with real citations from the API")

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

    # List of citations to verify (including multiple citations for the same case)
    citations_to_verify = [
        "410 U.S. 113",  # Roe v. Wade (U.S. Reports)
        "93 S. Ct. 705",  # Roe v. Wade (Supreme Court Reporter)
        "35 L. Ed. 2d 147",  # Roe v. Wade (Lawyers Edition)
        "196 Wash. 2d 725",  # Associated Press v. Washington State Legislature (Washington Reports)
        "455 P.3d 1164",  # Associated Press v. Washington State Legislature (Pacific Reporter)
        "190 Wash. 2d 1",  # WPEA v. Washington State Center for Childhood Deafness (Washington Reports)
        "183 Wash. 2d 490",  # State v. Arlene's Flowers (Washington Reports)
        "353 P.3d 1197",  # State v. Arlene's Flowers (Pacific Reporter)
    ]

    # Verify each citation
    verification_results = []
    for citation in citations_to_verify:
        print(f"\nVerifying citation: {citation}")
        result = verifier.verify_citation(citation)
        verification_results.append(result)
        print(f"Found: {result.get('found')}")
        print(f"Case Name: {result.get('case_name')}")
        print(f"URL: {result.get('url')}")

    # Group the verification results
    grouped_results = group_citations(verification_results)

    # Print grouped results
    print(
        f"\nGrouped {len(verification_results)} citations into {len(grouped_results)} groups:"
    )
    for i, group in enumerate(grouped_results):
        print(f"\nGroup {i+1}:")
        print(f"  Primary Citation: {group['citation']}")
        print(f"  Case Name: {group['case_name']}")
        print(f"  URL: {group['url']}")
        print(f"  Source: {group['source']}")

        if group.get("alternate_citations"):
            print(f"  Alternate Citations ({len(group['alternate_citations'])}):")
            for alt in group["alternate_citations"]:
                print(f"    - {alt['citation']} ({alt['source']})")

    # Save results to file
    with open("grouped_verification_results.json", "w", encoding="utf-8") as f:
        json.dump(grouped_results, f, indent=2)
    print("\nResults saved to grouped_verification_results.json")

    return grouped_results


if __name__ == "__main__":
    # Test with predefined citations
    test_citation_grouping()

    # Test with real citations from the API (optional)
    if len(sys.argv) > 1 and sys.argv[1] == "--with-api":
        test_with_real_citations()
