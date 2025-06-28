"""
Extract and Process Washington Court Briefs

This script is specifically designed to extract briefs from the Washington Courts website,
download them, extract citations, and verify them using the CaseStrainer system.
"""

import os
import sys
import json
import requests
import traceback
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Try to import from fixed_multi_source_verifier
try:
    from fixed_multi_source_verifier import MultiSourceVerifier

    print("Successfully imported MultiSourceVerifier from fixed_multi_source_verifier")
except ImportError:
    try:
        from multi_source_verifier import MultiSourceVerifier

        print("Successfully imported MultiSourceVerifier from multi_source_verifier")
    except ImportError:
        print("Error importing MultiSourceVerifier, trying to import from app_final")
        try:
            from app_final import check_case_with_ai

            print("Successfully imported check_case_with_ai from app_final")
        except ImportError:
            print("Error importing verification functions. Cannot proceed.")
            sys.exit(1)

# Try to import citation extraction function
try:
    from app_final import extract_citations

    print("Successfully imported extract_citations from app_final")
except ImportError:
    print("Error importing extract_citations. Cannot proceed.")
    sys.exit(1)

# Initialize the verifier with API keys from config.json
api_keys = {}
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        api_keys["courtlistener"] = config.get("courtlistener_api_key")

    multi_source_verifier = MultiSourceVerifier(api_keys)
    print("Successfully initialized MultiSourceVerifier with API keys")
except Exception as e:
    print(f"Error initializing MultiSourceVerifier: {e}")
    sys.exit(1)

# Constants
WA_COURTS_BASE_URL = "https://www.courts.wa.gov"
WA_COURTS_BRIEFS_URL = "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coaBriefs.home"
OUTPUT_FILE = "unverified_citations_with_sources.json"
DOWNLOADED_BRIEFS_DIR = "downloaded_briefs"
PROCESSED_BRIEFS_CACHE = "processed_briefs.json"

# Create directories if they don't exist
if not os.path.exists(DOWNLOADED_BRIEFS_DIR):
    os.makedirs(DOWNLOADED_BRIEFS_DIR)


def load_processed_briefs():
    """Load the list of already processed briefs."""
    if os.path.exists(PROCESSED_BRIEFS_CACHE):
        try:
            with open(PROCESSED_BRIEFS_CACHE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading processed briefs cache: {e}")
    return []


def save_processed_briefs(processed_briefs):
    """Save the list of processed briefs."""
    try:
        with open(PROCESSED_BRIEFS_CACHE, "w") as f:
            json.dump(processed_briefs, f)
    except Exception as e:
        print(f"Error saving processed briefs cache: {e}")


def get_court_of_appeals_links():
    """Get links to Court of Appeals divisions."""
    print(f"Fetching Court of Appeals divisions from {WA_COURTS_BRIEFS_URL}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(WA_COURTS_BRIEFS_URL, headers=headers)

        if response.status_code != 200:
            print(f"Error fetching Court of Appeals divisions: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # Look for links to divisions
        division_links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            text = link.text.strip().lower()
            if href and ("division" in text or "div." in text):
                full_url = urljoin(WA_COURTS_BASE_URL, href)
                division_links.append((text, full_url))

        print(f"Found {len(division_links)} Court of Appeals division links")
        return division_links

    except Exception as e:
        print(f"Error getting Court of Appeals division links: {e}")
        traceback.print_exc()
        return []


def get_brief_links_from_division(division_url, max_briefs=100):
    """Get links to briefs from a Court of Appeals division."""
    print(f"Fetching briefs from {division_url}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(division_url, headers=headers)

        if response.status_code != 200:
            print(f"Error fetching briefs from division: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # Find all links to PDFs
        brief_links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            text = link.text.strip().lower()
            if (
                href
                and href.endswith(".pdf")
                and ("brief" in text or "petition" in text or "motion" in text)
            ):
                full_url = urljoin(WA_COURTS_BASE_URL, href)
                brief_links.append(full_url)

        print(f"Found {len(brief_links)} brief links from division")

        # Limit to max_briefs
        return brief_links[:max_briefs]

    except Exception as e:
        print(f"Error getting brief links from division: {e}")
        traceback.print_exc()
        return []


def download_brief(brief_url):
    """Download a brief from a URL."""
    print(f"Downloading brief: {brief_url}")

    try:
        # Set up user agent to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Make the request
        response = requests.get(brief_url, headers=headers)

        if response.status_code != 200:
            print(f"Error downloading brief: {response.status_code}")
            return None

        # Save the brief
        filename = os.path.join(DOWNLOADED_BRIEFS_DIR, os.path.basename(brief_url))
        with open(filename, "wb") as f:
            f.write(response.content)

        return filename

    except Exception as e:
        print(f"Error downloading brief: {e}")
        traceback.print_exc()
        return None


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    print(f"Extracting text from PDF: {pdf_path}")

    try:
        # Try to import PyPDF2
        try:
            import PyPDF2
        except ImportError:
            print("PyPDF2 not installed. Please install it with 'pip install PyPDF2'.")
            return None

        # Open the PDF file
        with open(pdf_path, "rb") as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)

            # Extract text from each page
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()

            return text

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        traceback.print_exc()
        return None


def process_brief(brief_url, processed_briefs):
    """Process a brief to extract and verify citations."""
    print(f"Processing brief: {brief_url}")

    # Check if brief has already been processed
    if brief_url in processed_briefs:
        print(f"Brief already processed: {brief_url}")
        return []

    try:
        # Download the brief
        brief_path = download_brief(brief_url)
        if not brief_path:
            return []

        # Extract text from the brief
        brief_text = extract_text_from_pdf(brief_path)
        if not brief_text:
            return []

        # Extract citations from the text
        citations = extract_citations(brief_text)
        if not citations:
            print(f"No citations found in brief: {brief_url}")
            return []

        print(f"Found {len(citations)} citations in brief: {brief_url}")

        # Verify each citation
        unverified_citations = []
        for citation in citations:
            citation_text = citation.get("citation_text")
            if not citation_text:
                continue

            # Verify the citation
            result = multi_source_verifier.verify_citation(citation_text)

            # If citation is not verified, add it to the list
            if not result.get("found", False):
                unverified_citations.append(
                    {
                        "citation_text": citation_text,
                        "source_brief": brief_url,
                        "verification_result": result,
                    }
                )
                print(f"Unverified citation: {citation_text}")

            # Add a small delay to avoid overwhelming the API
            time.sleep(random.uniform(0.5, 1.5))

        # Mark brief as processed
        processed_briefs.append(brief_url)
        save_processed_briefs(processed_briefs)

        return unverified_citations

    except Exception as e:
        print(f"Error processing brief: {e}")
        traceback.print_exc()
        return []


def save_unverified_citations(unverified_citations):
    """Save unverified citations to a JSON file."""
    print(f"Saving {len(unverified_citations)} unverified citations to {OUTPUT_FILE}")

    try:
        # Load existing unverified citations if the file exists
        existing_citations = []
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, "r") as f:
                existing_citations = json.load(f)

        # Combine existing and new citations
        all_citations = existing_citations + unverified_citations

        # Remove duplicates based on citation_text and source_brief
        unique_citations = []
        seen = set()
        for citation in all_citations:
            key = (citation["citation_text"], citation["source_brief"])
            if key not in seen:
                seen.add(key)
                unique_citations.append(citation)

        # Save to file
        with open(OUTPUT_FILE, "w") as f:
            json.dump(unique_citations, f, indent=2)

        print(
            f"Saved {len(unique_citations)} unique unverified citations to {OUTPUT_FILE}"
        )

    except Exception as e:
        print(f"Error saving unverified citations: {e}")
        traceback.print_exc()


def main():
    """Main function to process briefs and extract unverified citations."""
    print("Starting extraction of unverified citations from Washington Court briefs")

    # Load processed briefs
    processed_briefs = load_processed_briefs()
    print(f"Loaded {len(processed_briefs)} previously processed briefs")

    # Get Court of Appeals division links
    division_links = get_court_of_appeals_links()

    # Process each division
    all_unverified_citations = []
    total_briefs_processed = 0

    for division_name, division_url in division_links:
        print(f"Processing division: {division_name} at {division_url}")

        # Get brief links from division
        brief_links = get_brief_links_from_division(division_url, max_briefs=20)

        # Filter out already processed briefs
        new_briefs = [brief for brief in brief_links if brief not in processed_briefs]
        print(f"Found {len(new_briefs)} new briefs to process in {division_name}")

        # Process each brief
        for i, brief_url in enumerate(new_briefs):
            print(
                f"Processing brief {i+1}/{len(new_briefs)} from {division_name}: {brief_url}"
            )
            unverified_citations = process_brief(brief_url, processed_briefs)
            all_unverified_citations.extend(unverified_citations)
            total_briefs_processed += 1

            # Save progress periodically
            if (i + 1) % 5 == 0 or i == len(new_briefs) - 1:
                save_unverified_citations(all_unverified_citations)

            # Add a small delay to avoid overwhelming the server
            time.sleep(random.uniform(1.0, 3.0))

            # Stop after processing 100 briefs total
            if total_briefs_processed >= 100:
                print("Reached limit of 100 briefs processed. Stopping.")
                break

        # Stop after processing 100 briefs total
        if total_briefs_processed >= 100:
            break

    # Save final results
    save_unverified_citations(all_unverified_citations)

    print("Finished extracting unverified citations from briefs")
    print(
        f"Found {len(all_unverified_citations)} unverified citations in {total_briefs_processed} briefs"
    )


if __name__ == "__main__":
    main()
