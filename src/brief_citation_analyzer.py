"""
DEPRECATED: This module is deprecated in favor of src/unified_citation_processor_v2.py
Use UnifiedCitationProcessorV2 instead for all new development.

This module will be removed in a future version.
"""

import warnings
warnings.warn(
    "BriefCitationAnalyzer is deprecated. Use UnifiedCitationProcessorV2 from src/unified_citation_processor_v2.py instead.",
    DeprecationWarning,
    stacklevel=2
)

import os
import sys
import json
import requests
import traceback
import time
import random
import re
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import functions from the correct modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from file_utils import extract_text_from_file
from unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

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
            logger.error(f"Error loading processed briefs cache: {e}")
    return []


def save_processed_briefs(processed_briefs):
    """Save the list of processed briefs."""
    try:
        with open(PROCESSED_BRIEFS_CACHE, "w") as f:
            json.dump(processed_briefs, f)
    except Exception as e:
        logger.error(f"Error saving processed briefs cache: {e}")


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

        # Save the brief
        filename = os.path.join(SAMPLE_BRIEFS_DIR, os.path.basename(brief_url))
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


def load_api_key():
    """Load the CourtListener API key from config.json."""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get("courtlistener_api_key")
    except Exception as e:
        logger.error(f"Error loading API key from config.json: {e}")
        return None


def process_brief(brief_url, processed_briefs):
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

        # Load the API key
        api_key = load_api_key()
        if not api_key:
            logger.info("No CourtListener API key found, cannot verify citations")
            return []

        # Query CourtListener API to verify citations using the processor
        courtlistener_results = processor.verify_citation_unified_workflow(citations[0]) if citations else None

        # Extract verified citations from CourtListener results
        verified_citations = []
        if courtlistener_results and "results" in courtlistener_results:
            for result in courtlistener_results["results"]:
                if "citation" in result:
                    verified_citations.append(result["citation"])

        logger.info(f"Found {len(verified_citations)} verified citations from CourtListener")

        # Find unverified citations
        unverified_citations = []
        for citation in citations:
            if citation not in verified_citations:
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
                        }
                    )
                    logger.info(f"Unverified citation with context: {citation}")
                else:
                    unverified_citations.append(
                        {
                            "citation_text": citation,
                            "source_brief": brief_url,
                            "context_before": "",
                            "context_after": "",
                            "full_context": "",
                        }
                    )
                    logger.info(f"Unverified citation without context: {citation}")

            # Add a small delay to avoid overwhelming the API
            time.sleep(random.uniform(0.5, 1.5))

        # Mark brief as processed
        processed_briefs.append(brief_url)
        save_processed_briefs(processed_briefs)

        return unverified_citations

    except Exception as e:
        logger.error(f"Error processing brief: {e}")
        traceback.print_exc()
        return []


def save_unverified_citations(unverified_citations):
    """Save unverified citations to a JSON file."""
    logger.info(f"Saving {len(unverified_citations)} unverified citations to {OUTPUT_FILE}")

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

        logger.info(f"Saved {len(unique_citations)} unique unverified citations to {OUTPUT_FILE}"
        )

    except Exception as e:
        logger.error(f"Error saving unverified citations: {e}")
        traceback.print_exc()


def main():
    """Main function to process briefs and extract unverified citations with context."""
    logger.info("Starting extraction of unverified citations with context from briefs")

    # Load processed briefs
    processed_briefs = load_processed_briefs()
    logger.info(f"Loaded {len(processed_briefs)} previously processed briefs")

    # Filter out already processed briefs
    new_briefs = [brief for brief in SAMPLE_BRIEF_URLS if brief not in processed_briefs]
    logger.info(f"Found {len(new_briefs)} new briefs to process")

    # Process each brief
    all_unverified_citations = []
    for i, brief_url in enumerate(new_briefs):
        logger.info(f"Processing brief {i+1}/{len(new_briefs)}: {brief_url}")
        unverified_citations = process_brief(brief_url, processed_briefs)
        all_unverified_citations.extend(unverified_citations)

        # Save progress periodically
        if (i + 1) % 5 == 0 or i == len(new_briefs) - 1:
            save_unverified_citations(all_unverified_citations)

        # Add a small delay to avoid overwhelming the server
        time.sleep(random.uniform(1.0, 3.0))

    # Save final results
    save_unverified_citations(all_unverified_citations)

    logger.info("Finished extracting unverified citations from briefs")
    logger.info(f"Found {len(all_unverified_citations)} unverified citations in {len(new_briefs)} briefs"
    )

    # Display the results in a more readable format
    if all_unverified_citations:
        logger.info("\nUnverified Citations with Context:")
        for i, citation in enumerate(all_unverified_citations):
            logger.info(f"\n{i+1}. Citation: {citation['citation_text']}")
            logger.info(f"   Source: {citation['source_brief']}")
            logger.info(f"   Context: ...{citation['context_before']} [{citation['citation_text']}] {citation['context_after']}...")


if __name__ == "__main__":
    main()
