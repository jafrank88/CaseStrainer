"""
Supreme Court Brief Downloader

This script downloads Supreme Court briefs from the Justice Department website,
extracts citations using CaseStrainer, and records unverified citations with context.
"""

import os
import sys
import json
import requests
import traceback
import time
import random
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Import eyecite for citation extraction if available
try:
    from eyecite import get_citations
    from eyecite.tokenizers import AhocorasickTokenizer

    logger.info("Successfully imported eyecite")
except ImportError:
    logger.warning("Warning: eyecite not installed. Will use CaseStrainer's extraction methods.")

# Import CaseStrainer functions
try:
    from src.file_utils import extract_text_from_file
    from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

    logger.info("Successfully imported CaseStrainer functions")
except ImportError:
    logger.error("Error: Could not import CaseStrainer functions. Make sure you're running this script from the CaseStrainer directory.")
    sys.exit(1)

# Constants
BRIEFS_DIR = "downloaded_briefs"
PROCESSED_BRIEFS_CACHE = "processed_briefs.json"
UNVERIFIED_CITATIONS_FILE = "unverified_citations.json"
CONTEXT_CHARS = 200  # Number of characters to include before and after the citation
MAX_BRIEFS = 100  # Maximum number of briefs to download
BASE_URL = "https://www.justice.gov/osg/supreme-court-briefs"
SEARCH_URL = "https://www.justice.gov/osg/supreme-court-briefs?text=&sc_term=All&type=All&subject=All&order=field_date&sort=desc&page="

# Create directories if they don't exist
if not os.path.exists(BRIEFS_DIR):
    os.makedirs(BRIEFS_DIR)


def load_processed_briefs():
    """Load the list of already processed briefs."""
    if os.path.exists(PROCESSED_BRIEFS_CACHE):
        try:
            with open(PROCESSED_BRIEFS_CACHE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading processed briefs cache: {e}")
    return []


def save_processed_briefs(processed_briefs):
    """Save the list of processed briefs."""
    try:
        with open(PROCESSED_BRIEFS_CACHE, "w") as f:
            json.dump(processed_briefs, f)
    except Exception as e:
        logger.error(f"Error saving processed briefs cache: {e}")


def get_brief_urls(page=0, max_pages=10):
    """Get brief URLs from the Justice Department website."""
    logger.info(f"Getting brief URLs from page {page}...")

    brief_urls = []

    try:
        # Set up user agent to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Make the request
        url = f"{SEARCH_URL}{page}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Error getting brief URLs: {response.status_code}")
            return brief_urls

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all PDF links
        pdf_links = soup.find_all(
            "a", href=lambda href: href and href.endswith("?inline")
        )

        for link in pdf_links:
            brief_url = urljoin(BASE_URL, link["href"])
            brief_urls.append(brief_url)

        # If we need more briefs and haven't reached the max pages, get more
        if len(brief_urls) < MAX_BRIEFS and page < max_pages - 1:
            brief_urls.extend(get_brief_urls(page + 1, max_pages))

        return brief_urls

    except Exception as e:
        logger.error(f"Error getting brief URLs: {e}")
        traceback.print_exc()
        return brief_urls


def download_brief(brief_url):
    """Download a brief from a URL."""
    logger.info(f"Downloading brief: {brief_url}")

    try:
        # Set up user agent to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Make the request
        response = requests.get(brief_url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Error downloading brief: {response.status_code}")
            return None

        # Generate a filename based on the URL
        filename = os.path.join(
            BRIEFS_DIR, os.path.basename(brief_url).replace("?inline", ".pdf")
        )

        # Save the brief
        with open(filename, "wb") as f:
            f.write(response.content)

        return filename

    except Exception as e:
        logger.error(f"Error downloading brief: {e}")
        traceback.print_exc()
        return None


def extract_citation_context(text, citation_text):
    """Extract the context around a citation."""
    logger.info(f"Extracting context for citation: {citation_text}")

    try:
        import re

        # Find all occurrences of the citation in the text
        citation_positions = []
        for match in re.finditer(re.escape(citation_text), text):
            start_pos = match.start()
            end_pos = match.end()
            citation_positions.append((start_pos, end_pos))

        if not citation_positions:
            logger.info(f"Citation not found in text: {citation_text}")
            return None

        # Extract context for each occurrence
        contexts = []
        for start_pos, end_pos in citation_positions:
            # Calculate context boundaries
            context_start = max(0, start_pos - CONTEXT_CHARS)
            context_end = min(len(text), end_pos + CONTEXT_CHARS)

            # Extract context
            context_before = text[context_start:start_pos]
            context_after = text[end_pos:context_end]
            full_context = context_before + citation_text + context_after

            contexts.append(
                {
                    "context_before": context_before,
                    "context_after": context_after,
                    "full_context": full_context,
                }
            )

        return contexts[0] if contexts else None

    except Exception as e:
        logger.error(f"Error extracting context for citation: {e}")
        traceback.print_exc()
        return None


def process_brief(brief_url, processed_briefs, verifier):
    """Process a brief to extract citations with context."""
    logger.info(f"Processing brief: {brief_url}")

    # Check if brief has already been processed
    if brief_url in processed_briefs:
        logger.info(f"Brief already processed: {brief_url}")
        return []

    try:
        # Download the brief
        brief_path = download_brief(brief_url)
        if not brief_path:
            return []

        # Extract text from the brief using the CaseStrainer function
        brief_text_result = extract_text_from_file(brief_path)
        if isinstance(brief_text_result, tuple):
            brief_text, _ = brief_text_result
        else:
            brief_text = brief_text_result
        if not brief_text:
            logger.info(f"No text extracted from brief: {brief_url}")
            return []

        # Extract citations from the text using the unified processor
        config = ProcessingConfig(
            use_eyecite=True,
            use_regex=True,
            extract_case_names=True,
            extract_dates=True,
            enable_clustering=True,
            enable_deduplication=True,
            enable_verification=True,
            debug_mode=True
        )
        processor = UnifiedCitationProcessorV2(config)
        citation_results = processor.process_text(brief_text)
        citations = [result.citation for result in citation_results]
        if not citations:
            logger.info(f"No citations found in brief: {brief_url}")
            return []

        logger.info(f"Found {len(citations)} citations in brief: {brief_url}")

        # Verify each citation using the MultiSourceVerifier
        unverified_citations = []
        for citation in citations:
            # Verify the citation using the unified processor
            result = processor.verify_citation_unified_workflow(citation)

            # If the citation is not verified, add it to the list
            if not result.get("verified", False):
                # Extract context for the citation
                context = extract_citation_context(brief_text, citation)

                if context:
                    unverified_citations.append(
                        {
                            "citation_text": citation,
                            "source_brief": brief_url,
                            "context_before": context["context_before"],
                            "context_after": context["context_after"],
                            "full_context": context["full_context"],
                            "verification_result": result,
                        }
                    )

        logger.info(f"Found {len(unverified_citations)} unverified citations in brief: {brief_url}"
        )

        # Add the brief to the processed list
        processed_briefs.append(brief_url)
        save_processed_briefs(processed_briefs)

        return unverified_citations

    except Exception as e:
        logger.error(f"Error processing brief: {e}")
        traceback.print_exc()
        return []


def save_unverified_citations(unverified_citations):
    """Save unverified citations to a JSON file."""
    logger.info(f"Saving {len(unverified_citations)} unverified citations...")

    try:
        # Load existing unverified citations if the file exists
        existing_citations = []
        if os.path.exists(UNVERIFIED_CITATIONS_FILE):
            try:
                with open(UNVERIFIED_CITATIONS_FILE, "r") as f:
                    existing_citations = json.load(f)
            except Exception as e:
                logger.error(f"Error loading existing unverified citations: {e}")

        # Add new unverified citations
        existing_citations.extend(unverified_citations)

        # Save the combined list
        with open(UNVERIFIED_CITATIONS_FILE, "w") as f:
            json.dump(existing_citations, f, indent=2)

        logger.info(f"Saved {len(unverified_citations)} unverified citations to {UNVERIFIED_CITATIONS_FILE}"
        )

    except Exception as e:
        logger.error(f"Error saving unverified citations: {e}")
        traceback.print_exc()


def main():
    """Main function to download and process briefs."""
    logger.info("Starting Supreme Court Brief Downloader...")

    # Load processed briefs
    processed_briefs = load_processed_briefs()
    logger.info(f"Loaded {len(processed_briefs)} previously processed briefs")

    # Create a unified processor for verification
    config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=True,
        debug_mode=True
    )
    verifier = UnifiedCitationProcessorV2(config)

    # Get brief URLs
    brief_urls = get_brief_urls()
    logger.info(f"Found {len(brief_urls)} brief URLs")

    # Limit to MAX_BRIEFS
    brief_urls = brief_urls[:MAX_BRIEFS]

    # Process each brief
    all_unverified_citations = []
    for brief_url in brief_urls:
        unverified_citations = process_brief(brief_url, processed_briefs, verifier)
        all_unverified_citations.extend(unverified_citations)

        # Save after each brief to avoid losing data
        save_unverified_citations(unverified_citations)

        # Add a small delay to avoid overwhelming the server
        time.sleep(random.uniform(1, 3))

    logger.info(f"Finished processing {len(brief_urls)} briefs")
    logger.info(f"Found {len(all_unverified_citations)} total unverified citations")


if __name__ == "__main__":
    main()
