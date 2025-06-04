"""
Test script to verify previously unconfirmed citations using the improved verification system.
"""

import json
import os
import sys
import traceback
from app_final_vue import is_landmark_case, search_citation_on_web, check_case_with_ai
from app_final_vue import get_cache_key, get_cache_path

# Load API keys
try:
    from app_final_vue import LANGSEARCH_API_KEY, COURTLISTENER_API_KEY

    print(
        f"Loaded API keys: LangSearch={LANGSEARCH_API_KEY[:5]}..., CourtListener={COURTLISTENER_API_KEY[:5]}..."
    )
except ImportError:
    print("Warning: API keys not loaded. Some verification methods may not work.")
    LANGSEARCH_API_KEY = None
    COURTLISTENER_API_KEY = None


# Load unconfirmed citations
def load_unconfirmed_citations():
    """Load unconfirmed citations from the JSON file."""
    try:
        with open("downloaded_briefs/all_unconfirmed_citations.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading unconfirmed citations: {e}")
        return {}


def test_citations(citations_to_test=20):
    """Test a selection of unconfirmed citations with our improved verification system."""
    all_citations = load_unconfirmed_citations()

    # Flatten the citations list
    flat_citations = []
    for document, citations in all_citations.items():
        for citation in citations:
            citation["document"] = document
            flat_citations.append(citation)

    # Take a sample of citations to test
    test_sample = flat_citations[:citations_to_test]
    print(f"Testing {len(test_sample)} unconfirmed citations...")

    results = {
        "newly_confirmed": [],
        "still_unconfirmed": [],
        "summary": {
            "total_tested": len(test_sample),
            "newly_confirmed_count": 0,
            "still_unconfirmed_count": 0,
        },
    }

    for citation in test_sample:
        citation_text = citation["citation_text"]
        case_name = citation.get("case_name")
        document = citation.get("document")

        print(f"\nTesting citation: {citation_text} ({case_name}) from {document}")

        # Clear cache for this citation to ensure fresh verification
        cache_key = get_cache_key(citation_text)
        cache_path = get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                os.remove(cache_path)
                print(f"Cleared cache for citation: {citation_text}")
            except Exception as e:
                print(f"Error clearing cache: {e}")

        # First check if it's a landmark case
        landmark_info = is_landmark_case(citation_text)
        if landmark_info:
            print(f"Found landmark case: {landmark_info['name']} ({citation_text})")
            result = {
                "found": True,
                "url": (
                    f"https://supreme.justia.com/cases/federal/us/{citation_text.split()[0]}/{citation_text.split()[2]}/"
                    if "U.S." in citation_text
                    else None
                ),
                "found_case_name": landmark_info["name"],
                "confidence": 0.95,
                "explanation": f"Verified landmark case: {landmark_info['name']} ({landmark_info['year']}) - {landmark_info['significance']}",
                "source": "Landmark Cases Database",
            }
            citation["verification_result"] = result
            results["newly_confirmed"].append(citation)
            results["summary"]["newly_confirmed_count"] += 1
            continue

        # Try web search
        try:
            web_result = search_citation_on_web(citation_text, case_name)
            if web_result.get("found", False):
                print(f"Web search confirmed citation: {citation_text}")
                citation["verification_result"] = web_result
                results["newly_confirmed"].append(citation)
                results["summary"]["newly_confirmed_count"] += 1
                continue
        except Exception as e:
            print(f"Error in web search: {e}")
            traceback.print_exc()

        # If web search doesn't find it, try with AI
        if LANGSEARCH_API_KEY:
            try:
                ai_result = check_case_with_ai(citation_text, case_name)
                if ai_result.get("found", False):
                    print(f"AI verification confirmed citation: {citation_text}")
                    citation["verification_result"] = ai_result
                    results["newly_confirmed"].append(citation)
                    results["summary"]["newly_confirmed_count"] += 1
                    continue
            except Exception as e:
                print(f"Error in AI verification: {e}")
                traceback.print_exc()

        # If we get here, the citation is still unconfirmed
        print(f"Citation still unconfirmed: {citation_text}")
        results["still_unconfirmed"].append(citation)
        results["summary"]["still_unconfirmed_count"] += 1

    # Calculate percentage of newly confirmed citations
    total = results["summary"]["total_tested"]
    newly_confirmed = results["summary"]["newly_confirmed_count"]
    percentage = (newly_confirmed / total) * 100 if total > 0 else 0
    results["summary"]["percentage_confirmed"] = round(percentage, 2)

    return results


def save_results(results, filename="citation_verification_results.json"):
    """Save the verification results to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {filename}")
    except Exception as e:
        print(f"Error saving results: {e}")


if __name__ == "__main__":
    # Number of citations to test
    num_citations = 20
    if len(sys.argv) > 1:
        try:
            num_citations = int(sys.argv[1])
        except ValueError:
            print(
                f"Invalid number of citations: {sys.argv[1]}. Using default: {num_citations}"
            )

    # Run the test
    results = test_citations(num_citations)

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
            if result.get("url"):
                print(f"   URL: {result['url']}")
            print()

    # Save the results
    save_results(results)
