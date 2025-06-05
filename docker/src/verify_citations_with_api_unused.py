"""
Citation Verification with CourtListener API

This script verifies citations using the CourtListener API with proper authentication
and cleans up the unverified citations file to contain only truly unverified citations.
"""

import json
import requests
import traceback
import time

# Constants
UNVERIFIED_CITATIONS_FILE = "fresh_unverified_citations.json"
VERIFIED_CITATIONS_FILE = "verified_citations.json"
TRULY_UNVERIFIED_CITATIONS_FILE = "truly_unverified_citations.json"
UNCONFIRMED_CITATIONS_TAB_FILE = "Unconfirmed_Citations_Tab.txt"
CONFIG_FILE = "config.json"
API_REQUEST_DELAY = 1  # Seconds between API requests to avoid rate limiting


def load_api_key():
    """Load the CourtListener API key from config.json."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return config.get("courtlistener_api_key")
    except Exception as e:
        print(f"Error loading API key from config.json: {e}")
        return None


def load_unverified_citations():
    """Load unverified citations from the JSON file."""
    try:
        with open(UNVERIFIED_CITATIONS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading unverified citations: {e}")
        return []


def save_citations(citations, filename):
    """Save citations to a JSON file."""
    try:
        with open(filename, "w") as f:
            json.dump(citations, f, indent=2)
        print(f"Saved {len(citations)} citations to {filename}")
    except Exception as e:
        print(f"Error saving citations to {filename}: {e}")


def verify_citation_with_api(citation, api_key):
    """Verify a citation using the CourtListener API with authentication."""
    print(f"Verifying citation with API: {citation}")

    try:
        # Set up headers with API key
        headers = {
            "Authorization": f"Token {api_key}",
            "User-Agent": "CaseStrainer Citation Verifier (https://github.com/jafrank88/CaseStrainer)",
        }

        # Clean the citation for URL
        clean_citation = citation.replace(" ", "+")

        # Make the request to CourtListener API
        url = f"https://www.courtlistener.com/api/rest/v3/search/?type=o&q={clean_citation}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Error verifying citation: {response.status_code}")
            return False, None

        # Parse the response
        data = response.json()

        # Check if the citation was found
        if data.get("count", 0) > 0:
            print(f"Citation verified: {citation}")
            return True, data

        print(f"Citation not verified: {citation}")
        return False, data

    except Exception as e:
        print(f"Error verifying citation: {e}")
        traceback.print_exc()
        return False, None


def create_unconfirmed_citations_tab(unverified_citations):
    """Create a tab-formatted file for the Unconfirmed Citations tab."""
    print("Creating Unconfirmed Citations tab file...")

    try:
        with open(UNCONFIRMED_CITATIONS_TAB_FILE, "w", encoding="utf-8") as f:
            f.write("Citation\tBrief URL\tContext\n")

            for citation in unverified_citations:
                citation_text = citation["citation_text"]
                brief_url = citation["brief_url"]
                context = citation["full_context"].replace("\n", " ").replace("\t", " ")

                f.write(f"{citation_text}\t{brief_url}\t{context}\n")

        print(
            f"Created Unconfirmed Citations tab file: {UNCONFIRMED_CITATIONS_TAB_FILE}"
        )

    except Exception as e:
        print(f"Error creating Unconfirmed Citations tab file: {e}")
        traceback.print_exc()


def main():
    """Main function to verify citations and clean up the unverified citations file."""
    print("Starting Citation Verification with CourtListener API...")

    # Load the API key
    api_key = load_api_key()
    if not api_key:
        print("No CourtListener API key found in config.json. Cannot proceed.")
        return

    print(f"Loaded CourtListener API key: {api_key[:5]}...")

    # Load unverified citations
    unverified_citations = load_unverified_citations()
    print(f"Loaded {len(unverified_citations)} unverified citations")

    # Verify each citation
    verified_citations = []
    truly_unverified_citations = []

    for i, citation_data in enumerate(unverified_citations):
        citation_text = citation_data["citation_text"]
        print(
            f"Processing citation {i+1} of {len(unverified_citations)}: {citation_text}"
        )

        # Verify the citation
        verified, api_data = verify_citation_with_api(citation_text, api_key)

        # Add to the appropriate list
        if verified:
            citation_data["verification_data"] = api_data
            verified_citations.append(citation_data)
        else:
            truly_unverified_citations.append(citation_data)

        # Add a delay to avoid rate limiting
        time.sleep(API_REQUEST_DELAY)

    # Save the results
    save_citations(verified_citations, VERIFIED_CITATIONS_FILE)
    save_citations(truly_unverified_citations, TRULY_UNVERIFIED_CITATIONS_FILE)

    # Create the Unconfirmed Citations tab file
    create_unconfirmed_citations_tab(truly_unverified_citations)

    print("Citation verification complete")
    print(f"Found {len(verified_citations)} verified citations")
    print(f"Found {len(truly_unverified_citations)} truly unverified citations")
    print(f"Verified citations saved to {VERIFIED_CITATIONS_FILE}")
    print(f"Truly unverified citations saved to {TRULY_UNVERIFIED_CITATIONS_FILE}")
    print(f"Unconfirmed Citations tab file created at {UNCONFIRMED_CITATIONS_TAB_FILE}")


if __name__ == "__main__":
    main()
