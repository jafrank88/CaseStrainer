"""
Context Citation Extractor

This script downloads sample briefs, uses eyecite to extract citations,
and saves unverified citations along with the source brief URL and surrounding context.
"""

import os
import sys
import json
import requests
import traceback
import time
import random
from datetime import datetime
from urllib.parse import urljoin

# Import eyecite for citation extraction
try:
    from eyecite import get_citations
    from eyecite.tokenizers import HyperscanTokenizer

    print("Successfully imported eyecite")
except ImportError:
    print("Error: eyecite not installed. Please install it with 'pip install eyecite'")
    sys.exit(1)

# Constants
OUTPUT_FILE = "unverified_citations_with_context.json"
SAMPLE_BRIEFS_DIR = "sample_briefs"
PROCESSED_BRIEFS_CACHE = "processed_briefs.json"
CONTEXT_CHARS = 200  # Number of characters to include before and after the citation

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


def extract_citations_with_context(text):
    """Extract citations using eyecite and include surrounding context."""
    print("Extracting citations using eyecite")

    try:
        # Use eyecite to extract citations
        citations = get_citations(text, tokenizer=HyperscanTokenizer())

        # Convert to our format with context
        formatted_citations = []
        for citation in citations:
            # Get the citation text
            citation_text = citation.matched_text()

            # Get start and end positions
            start_pos = citation.span()[0]
            end_pos = citation.span()[1]

            # Calculate context boundaries
            context_start = max(0, start_pos - CONTEXT_CHARS)
            context_end = min(len(text), end_pos + CONTEXT_CHARS)

            # Extract context
            context_before = text[context_start:start_pos]
            context_after = text[end_pos:context_end]

            # Extract likely case name from context_before using utility function
            from extract_case_name import extract_case_name_from_context

            extracted_case_name = extract_case_name_from_context(context_before)

            # Add to our list
            formatted_citations.append(
                {
                    "citation_text": citation_text,
                    "start_index": start_pos,
                    "end_index": end_pos,
                    "context_before": context_before,
                    "context_after": context_after,
                    "full_context": context_before + citation_text + context_after,
                    "citation_type": str(citation.type()),
                    "metadata": {
                        "reporter": getattr(citation, "reporter", None),
                        "volume": getattr(citation, "volume", None),
                        "page": getattr(citation, "page", None),
                        "year": getattr(citation, "year", None),
                    },
                    "extracted_case_name": extracted_case_name,
                }
            )

        print(f"Found {len(formatted_citations)} citations using eyecite")
        return formatted_citations

    except Exception as e:
        print(f"Error extracting citations with eyecite: {e}")
        traceback.print_exc()
        return []


def check_citation_in_courtlistener(citation_text):
    """Simple check if citation exists in CourtListener."""
    print(f"Checking citation in CourtListener: {citation_text}")

    try:
        # Load API key from config.json
        api_key = None
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                api_key = config.get("courtlistener_api_key")
        except Exception as e:
            print(f"Error loading API key from config.json: {e}")
            return False

        if not api_key:
            print("No CourtListener API key found")
            return False

        # Set up headers with API key
        headers = {
            "Authorization": f"Token {api_key}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }

        # Prepare search query
        params = {"citation": citation_text, "format": "json"}

        # Make the request
        response = requests.get(
            "https://www.courtlistener.com/api/rest/v3/search/",
            headers=headers,
            params=params,
        )

        if response.status_code != 200:
            print(f"Error checking citation in CourtListener: {response.status_code}")
            return False

        # Parse the response
        data = response.json()

        # Check if any results were found
        if data.get("count", 0) > 0:
            print(f"Citation found in CourtListener: {citation_text}")
            return True
        else:
            print(f"Citation not found in CourtListener: {citation_text}")
            return False

    except Exception as e:
        print(f"Error checking citation in CourtListener: {e}")
        traceback.print_exc()
        return False


def process_brief(brief_url, processed_briefs):
    """Process a brief to extract citations with context."""
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

        # Extract citations from the text using eyecite
        citations = extract_citations_with_context(brief_text)
        if not citations:
            print(f"No citations found in brief: {brief_url}")
            return []

        print(f"Found {len(citations)} citations in brief: {brief_url}")

        # Check each citation in CourtListener
        unverified_citations = []
        for citation in citations:
            citation_text = citation.get("citation_text")
            if not citation_text:
                continue

            # Check if citation exists in CourtListener
            found = check_citation_in_courtlistener(citation_text)

            # If citation is not verified, add it to the list
            if not found:
                unverified_citations.append(
                    {
                        "citation_text": citation_text,
                        "source_brief": brief_url,
                        "citation_metadata": citation.get("metadata", {}),
                        "context_before": citation.get("context_before", ""),
                        "context_after": citation.get("context_after", ""),
                        "full_context": citation.get("full_context", ""),
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
    """Main function to process briefs and extract unverified citations with context."""
    print("Starting extraction of unverified citations with context from sample briefs")

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
        unverified_citations = process_brief(brief_url, processed_briefs)
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

    # Display the results in a more readable format
    if all_unverified_citations:
        print("\nUnverified Citations with Context:")
        for i, citation in enumerate(all_unverified_citations):
            print(f"\n{i+1}. Citation: {citation['citation_text']}")
            print(f"   Source: {citation['source_brief']}")
            print(
                f"   Context: ...{citation['context_before']} [{citation['citation_text']}] {citation['context_after']}..."
            )


if __name__ == "__main__":
    main()
