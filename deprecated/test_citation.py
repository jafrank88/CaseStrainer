from src.citation_verification import CitationVerifier
import json
import requests


def test_citation():
    # Initialize the verifier with the API key from config
    import os

    api_key = os.environ.get("COURTLISTENER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "COURTLISTENER_API_KEY environment variable not set. Please set it before running this test."
        )
    verifier = CitationVerifier(api_key=api_key)

    # Test the citation
    citation = "339 U.S. 629"
    result = verifier.verify_citation(citation)

    # Print the result
    print("\nVerification Result:")
    print(json.dumps(result, indent=2))


def post_citation():
    url = "http://localhost:5000/api/validate_citations"
    data = {"text": "92 U.S. 214"}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    print(response.status_code)
    print(response.json())


if __name__ == "__main__":
    test_citation()
    post_citation()
