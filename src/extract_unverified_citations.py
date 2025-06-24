"""
Extract Unverified Citations from Briefs

This script processes a set of briefs from Washington Courts,
extracts citations, verifies them, and saves unverified citations
along with the source brief URL.
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
from src.enhanced_multi_source_verifier import verify_citation

# Try to import from app_final_vue.py
try:
    from app_final_vue import extract_citations, check_case_with_ai

    print("Successfully imported functions from app_final_vue.py")
except ImportError:
    print("Warning: Could not import functions from app_final_vue.py")
    sys.exit(1)

# Washington Courts URLs
WA_COURTS_BASE_URL = "https://www.courts.wa.gov"
WA_COURTS_BRIEFS_URL = "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coaBriefs.home"

# Output file for unverified citations
OUTPUT_FILE = "unverified_citations_with_sources.json"

# Cache file to avoid reprocessing the same briefs
PROCESSED_BRIEFS_CACHE = "processed_briefs.json"


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


def get_brief_links(page_url, max_briefs=100):
    """Get links to briefs from Washington Courts website."""
    print(f"Fetching briefs from {page_url}")

    try:
        # Set up user agent to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Make the request
        response = requests.get(page_url, headers=headers)

        if response.status_code != 200:
            print(f"Error fetching briefs: {response.status_code}")
            return []

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all links to briefs
        brief_links = []

        # Look for links in tables
        for table in soup.find_all("table"):
            for link in table.find_all("a"):
                href = link.get("href")
                if href and href.endswith(".pdf"):
                    # Check if it's a brief link
                    link_text = link.text.lower()
                    if "brief" in link_text or "petition" in link_text:
                        full_url = urljoin(WA_COURTS_BASE_URL, href)
                        brief_links.append(full_url)

        # If no briefs found in tables, try all links
        if not brief_links:
            for link in soup.find_all("a"):
                href = link.get("href")
                if href and href.endswith(".pdf"):
                    full_url = urljoin(WA_COURTS_BASE_URL, href)
                    brief_links.append(full_url)

        print(f"Found {len(brief_links)} brief links before filtering")

        # Limit to max_briefs
        return brief_links[:max_briefs]

    except Exception as e:
        print(f"Error getting brief links: {e}")
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
        try:
            response = requests.get(brief_url, headers=headers, timeout=30)
        except requests.Timeout:
            print(f"Timeout occurred while downloading {brief_url}")
            return None

        if response.status_code != 200:
            print(f"Error downloading brief: {response.status_code}")
            return None

        # Create downloads directory if it doesn't exist
        if not os.path.exists("downloaded_briefs"):
            os.makedirs("downloaded_briefs")

        # Save the brief
        filename = os.path.join("downloaded_briefs", os.path.basename(brief_url))
        with open(filename, "wb") as f:
            f.write(response.content)

        return filename

    except Exception as e:
        print(f"Error downloading brief: {e}")
        traceback.print_exc()
        return None


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file using pdfminer.six, with PyPDF2 as fallback."""
    print(f"Extracting text from PDF: {pdf_path}")
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract_text
        text = pdfminer_extract_text(pdf_path)
        if text and text.strip():
            print("pdfminer.six succeeded.")
            return text
        else:
            print("pdfminer.six extracted no text, trying PyPDF2...")
    except Exception as e:
        print(f"pdfminer.six failed: {e}")
    try:
        import PyPDF2
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text and text.strip():
            print("PyPDF2 succeeded.")
            return text
        else:
            print("PyPDF2 also extracted no text.")
            return None
    except Exception as e:
        print(f"PyPDF2 failed: {e}")
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
            result = verify_citation(citation_text)

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
    print("Starting extraction of unverified citations from briefs")

    # Load processed briefs
    processed_briefs = load_processed_briefs()
    print(f"Loaded {len(processed_briefs)} previously processed briefs")

    # Get brief links
    brief_links = get_brief_links(WA_COURTS_BRIEFS_URL, max_briefs=100)
    print(f"Found {len(brief_links)} brief links")

    # Filter out already processed briefs
    new_briefs = [brief for brief in brief_links if brief not in processed_briefs]
    print(f"Found {len(new_briefs)} new briefs to process")

    # Process each brief
    all_unverified_citations = []
    for i, brief_url in enumerate(new_briefs):
        print(f"Processing brief {i+1}/{len(new_briefs)}: {brief_url}")
        unverified_citations = process_brief(brief_url, processed_briefs)
        all_unverified_citations.extend(unverified_citations)

        # Save progress periodically
        if (i + 1) % 10 == 0 or i == len(new_briefs) - 1:
            save_unverified_citations(all_unverified_citations)

        # Add a small delay to avoid overwhelming the server
        time.sleep(random.uniform(1.0, 3.0))

    # Save final results
    save_unverified_citations(all_unverified_citations)

    print("Finished extracting unverified citations from briefs")
    print(
        f"Found {len(all_unverified_citations)} unverified citations in {len(new_briefs)} briefs"
    )


if __name__ == "__main__":
    main()
