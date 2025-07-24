#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Analyze Confirmed Citations

This script analyzes 100 confirmed citations from CourtListener to check if they
contain any unconfirmed citations within their text. This helps identify cases
where even verified citations might contain problematic references.
"""

import os
import json
import time
import requests
import traceback
from bs4 import BeautifulSoup
import sys

# Prevent use of v3 CourtListener API endpoints
# Check all API URLs in the script for v3 endpoints
api_urls = [
    "https://www.courtlistener.com/api/rest/v4/search/",
]
for url in api_urls:
    if 'v3' in url:
        print("ERROR: v3 CourtListener API endpoint detected. Please use v4 only.")
        sys.exit(1)

# Import functions from analyze_more_briefs.py
from analyze_more_briefs import extract_unconfirmed_citations, DOWNLOAD_DIR

# Directory for storing confirmed cases
CONFIRMED_DIR = os.path.join(DOWNLOAD_DIR, "confirmed_cases")
os.makedirs(CONFIRMED_DIR, exist_ok=True)

# CourtListener API URL
COURTLISTENER_API_URL = "https://www.courtlistener.com/api/rest/v4/search/"


# Load API key from config.json
def load_api_key():
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get("courtlistener_api_key")
    except Exception as e:
        print(f"Error loading API key: {e}")
        return None


def fetch_confirmed_cases(api_key, count=100):
    """
    Fetch confirmed cases from CourtListener API
    """
    if not api_key:
        print("No API key provided")
        return []

    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}

    # Parameters for the search
    params = {
        "type": "o",  # Opinion type
        "order_by": "score desc",  # Order by relevance score
        "stat_Precedential": "on",  # Precedential opinions only
        "court": "wash",  # Washington courts
        "page_size": count,  # Number of results to fetch
    }

    try:
        print(f"Fetching {count} confirmed cases from CourtListener...")
        response = requests.get(COURTLISTENER_API_URL, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            print(f"Successfully fetched {len(results)} cases")
            return results
        else:
            print(f"API request failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return []

    except Exception as e:
        print(f"Error fetching confirmed cases: {e}")
        traceback.print_exc()
        return []


def download_case_text(case_id, absolute_url):
    """
    Download the full text of a case from CourtListener
    """
    case_filename = f"case_{case_id}.txt"
    case_path = os.path.join(CONFIRMED_DIR, case_filename)

    # Check if already downloaded
    if os.path.exists(case_path):
        print(f"Case {case_id} already downloaded")
        with open(case_path, "r", encoding="utf-8") as f:
            return case_path, f.read()

    # Full URL to the case
    full_url = f"https://www.courtlistener.com{absolute_url}"

    try:
        print(f"Downloading case {case_id} from {full_url}")
        response = requests.get(full_url)

        if response.status_code == 200:
            # Parse HTML to extract the opinion text
            soup = BeautifulSoup(response.text, "html.parser")
            opinion_text = soup.find("div", class_="opinion-text")

            if opinion_text:
                text = opinion_text.get_text(separator="\n")

                # Save to file
                with open(case_path, "w", encoding="utf-8") as f:
                    f.write(text)

                print(f"Case {case_id} downloaded and saved to {case_path}")
                return case_path, text
            else:
                print(f"Could not find opinion text for case {case_id}")
                return None, None
        else:
            print(f"Failed to download case {case_id}: HTTP {response.status_code}")
            return None, None

    except Exception as e:
        print(f"Error downloading case {case_id}: {e}")
        traceback.print_exc()
        return None, None


def analyze_case_with_casestrainer(case_path, case_text, api_key):
    """
    Analyze a case using CaseStrainer to find unconfirmed citations
    """
    from app_final_vue import run_analysis, generate_analysis_id

    print(f"Analyzing case: {os.path.basename(case_path)}")

    # Check if results already exist
    results_file = f"{os.path.splitext(case_path)[0]}_results.json"
    if os.path.exists(results_file):
        print(f"Analysis results already exist: {os.path.basename(results_file)}")
        with open(results_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Generate a unique analysis ID
    analysis_id = generate_analysis_id()

    # Run the analysis
    result = run_analysis(analysis_id, brief_text=case_text, api_key=api_key)

    # Save the results
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Analysis completed and saved to {results_file}")
    return result


def main():
    """
    Main function to analyze confirmed cases for unconfirmed citations
    """
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("No API key found in config.json")
        return

    # Fetch confirmed cases
    confirmed_cases = fetch_confirmed_cases(api_key, count=100)
    if not confirmed_cases:
        print("No confirmed cases found")
        return

    # Dictionary to store cases with unconfirmed citations
    cases_with_unconfirmed = {}

    # Process each confirmed case
    for i, case in enumerate(confirmed_cases, 1):
        case_id = case.get("id")
        absolute_url = case.get("absolute_url")
        case_name = case.get("case_name", "Unknown Case")

        print(f"\n[{i}/100] Processing case: {case_name} (ID: {case_id})")

        # Download case text
        case_path, case_text = download_case_text(case_id, absolute_url)
        if not case_path or not case_text:
            print(f"Skipping case {case_id} due to download failure")
            continue

        # Analyze the case with CaseStrainer
        analysis_result = analyze_case_with_casestrainer(case_path, case_text, api_key)

        # Extract unconfirmed citations
        unconfirmed = extract_unconfirmed_citations(analysis_result, case_path)

        if unconfirmed:
            print(
                f"Found {len(unconfirmed)} unconfirmed citations in confirmed case {case_id}"
            )
            cases_with_unconfirmed[case_id] = {
                "case_name": case_name,
                "case_url": f"https://www.courtlistener.com{absolute_url}",
                "unconfirmed_citations": unconfirmed,
            }

            # Print unconfirmed citations
            for j, citation in enumerate(unconfirmed, 1):
                print(f"  {j}. {citation['citation_text']} - {citation['case_name']}")
                print(f"     Confidence: {citation['confidence']}")
                print(f"     Explanation: {citation['explanation']}")
        else:
            print(f"No unconfirmed citations found in case {case_id}")

        # Save intermediate results
        if cases_with_unconfirmed:
            results_file = os.path.join(
                CONFIRMED_DIR, "confirmed_cases_with_unconfirmed.json"
            )
            with open(results_file, "w", encoding="utf-8") as f:
                json.dump(cases_with_unconfirmed, f, indent=2)
            print(f"Saved intermediate results to {results_file}")

        # Sleep to avoid overwhelming the API
        time.sleep(2)

    # Print final summary
    print("\n=== FINAL SUMMARY ===")
    total_cases_with_unconfirmed = len(cases_with_unconfirmed)
    total_unconfirmed = sum(
        len(case_data["unconfirmed_citations"])
        for case_data in cases_with_unconfirmed.values()
    )

    print(f"Analyzed {len(confirmed_cases)} confirmed cases")
    print(
        f"Found {total_unconfirmed} unconfirmed citations in {total_cases_with_unconfirmed} confirmed cases"
    )

    # Save final results
    if cases_with_unconfirmed:
        # Save detailed results
        results_file = os.path.join(
            CONFIRMED_DIR, "confirmed_cases_with_unconfirmed.json"
        )
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(cases_with_unconfirmed, f, indent=2)
        print(f"Results saved to {results_file}")

        # Also save a flattened list for easier access
        flattened_citations = []
        for case_id, case_data in cases_with_unconfirmed.items():
            for citation in case_data["unconfirmed_citations"]:
                citation["source_case_id"] = case_id
                citation["source_case_name"] = case_data["case_name"]
                citation["source_case_url"] = case_data["case_url"]
                citation["source_file"] = (
                    f"confirmed_case_{case_id}.txt"  # Create a source filename for display
                )
                flattened_citations.append(citation)

        flattened_file = os.path.join(
            CONFIRMED_DIR, "confirmed_cases_unconfirmed_citations_flat.json"
        )
        with open(flattened_file, "w", encoding="utf-8") as f:
            json.dump(flattened_citations, f, indent=2)
        print(f"Flattened results saved to {flattened_file}")

        # Merge with existing unconfirmed citations
        try:
            # Load existing unconfirmed citations
            existing_file = os.path.join(
                DOWNLOAD_DIR, "unconfirmed_citations_flat.json"
            )
            if os.path.exists(existing_file):
                with open(existing_file, "r", encoding="utf-8") as f:
                    existing_citations = json.load(f)
                print(
                    f"Loaded {len(existing_citations)} existing unconfirmed citations"
                )

                # Merge the two lists
                combined_citations = existing_citations + flattened_citations
                print(
                    f"Combined total: {len(combined_citations)} unconfirmed citations"
                )

                # Save the combined list
                with open(existing_file, "w", encoding="utf-8") as f:
                    json.dump(combined_citations, f, indent=2)
                print(
                    f"Added {len(flattened_citations)} new unconfirmed citations to the main database"
                )
            else:
                print(
                    f"No existing unconfirmed citations file found at {existing_file}"
                )
                # Copy our flattened file to the main location
                import shutil

                shutil.copy(flattened_file, existing_file)
                print(
                    f"Created new unconfirmed citations database with {len(flattened_citations)} citations"
                )
        except Exception as e:
            print(f"Error merging with existing unconfirmed citations: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
