"""
Sample Citation Extractor

This script processes a sample set of briefs, extracts citations,
verifies them using the fixed_multi_source_verifier, and saves
unverified citations along with the source brief URL.
"""

import os
import sys
import json
import requests
import re
import traceback
import time
import random

# Import the fixed multi-source verifier
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fixed_multi_source_verifier import MultiSourceVerifier

# Constants
OUTPUT_FILE = "unverified_citations_with_sources.json"
SAMPLE_BRIEFS_DIR = "sample_briefs"
PROCESSED_BRIEFS_CACHE = "processed_briefs.json"

# Create directories if they don't exist
if not os.path.exists(SAMPLE_BRIEFS_DIR):
    os.makedirs(SAMPLE_BRIEFS_DIR)

# Sample brief URLs - these are example URLs, replace with actual brief URLs
SAMPLE_BRIEF_URLS = [
    "https://www.courts.wa.gov/content/Briefs/A01/789301%20Appellant%20Thurston%20County.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/789301%20Respondent%20Black%20Hills.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/789301%20Respondent%20Confederated%20Tribes.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/789301%20Respondent%20Squaxin.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/789301%20Respondent.pdf",
]


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
        filename = os.path.join(SAMPLE_BRIEFS_DIR, os.path.basename(brief_url))
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


def extract_citations(text):
    """Extract citations from text."""
    print("Extracting citations from text")

    # Simple citation patterns
    citation_patterns = [
        r"\d+\s+U\.S\.\s+\d+",  # U.S. Reports
        r"\d+\s+S\.\s*Ct\.\s+\d+",  # Supreme Court Reporter
        r"\d+\s+L\.\s*Ed\.\s+\d+",  # Lawyers Edition
        r"\d+\s+F\.\d*\s+\d+",  # Federal Reporter
        r"\d+\s+F\.\s*Supp\.\s+\d+",  # Federal Supplement
        r"\d+\s+F\.\s*R\.\s*D\.\s+\d+",  # Federal Rules Decisions
        r"\d+\s+B\.\s*R\.\s+\d+",  # Bankruptcy Reporter
        r"\d+\s+Wn\.\s*2d\s+\d+",  # Washington Reports 2d
        r"\d+\s+Wn\.\s*App\.\s+\d+",  # Washington Appellate Reports
        r"\d+\s+P\.\d*\s+\d+",  # Pacific Reporter
        r"\d+\s+A\.\d*\s+\d+",  # Atlantic Reporter
        r"\d+\s+N\.\s*E\.\d*\s+\d+",  # North Eastern Reporter
        r"\d+\s+N\.\s*W\.\d*\s+\d+",  # North Western Reporter
        r"\d+\s+S\.\s*E\.\d*\s+\d+",  # South Eastern Reporter
        r"\d+\s+S\.\s*W\.\d*\s+\d+",  # South Western Reporter
        r"\d+\s+So\.\d*\s+\d+",  # Southern Reporter
        r"\d{4}\s+WL\s+\d+",  # Westlaw
    ]

    # Combine patterns
    combined_pattern = "|".join(citation_patterns)

    # Find all citations
    citations = []
    for match in re.finditer(combined_pattern, text):
        citation_text = match.group(0)
        citations.append(
            {
                "citation_text": citation_text,
                "start_index": match.start(),
                "end_index": match.end(),
            }
        )

    print(f"Found {len(citations)} citations")
    return citations


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
            result = verify_citation(citation_text, use_database=True)

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
    print("Starting extraction of unverified citations from sample briefs")

    # Load processed briefs
    processed_briefs = load_processed_briefs()
    print(f"Loaded {len(processed_briefs)} previously processed briefs")

    # Filter out already processed briefs
    new_briefs = [brief for brief in SAMPLE_BRIEF_URLS if brief not in processed_briefs]
    print(f"Found {len(new_briefs)} new briefs to process")

    # Process each brief
    all_unverified_citations = []
    for i, brief_url in enumerate(new_briefs):
        print(f"Processing brief {i+1}/{len(new_briefs)}: {brief_url}")
        unverified_citations = process_brief(
            brief_url, processed_briefs
        )
        all_unverified_citations.extend(unverified_citations)

        # Save progress periodically
        if (i + 1) % 5 == 0 or i == len(new_briefs) - 1:
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
