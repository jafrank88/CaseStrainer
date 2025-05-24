"""
Extract and Process Washington Court Briefs (Slow Version)

This script is a modified version of extract_wa_court_briefs.py designed to:
1. Download briefs at a slower rate to avoid rate limiting
2. Process a smaller number of briefs
3. Ensure proper error handling and logging
"""

import os
import sys
import json
import requests
import re
import traceback
import time
import random
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("wa_briefs_extraction.log"), logging.StreamHandler()],
)
logger = logging.getLogger("wa_briefs_extractor")

# Try to import from fixed_multi_source_verifier
try:
    from fixed_multi_source_verifier import MultiSourceVerifier

    logger.info(
        "Successfully imported MultiSourceVerifier from fixed_multi_source_verifier"
    )
except ImportError:
    try:
        from multi_source_verifier import MultiSourceVerifier

        logger.info(
            "Successfully imported MultiSourceVerifier from multi_source_verifier"
        )
    except ImportError:
        logger.error(
            "Error importing MultiSourceVerifier, trying to import from app_final"
        )
        try:
            from app_final import check_case_with_ai

            logger.info("Successfully imported check_case_with_ai from app_final")
        except ImportError:
            logger.error("Error importing verification functions. Cannot proceed.")
            sys.exit(1)

# Try to import citation extraction function
try:
    from app_final import extract_citations

    logger.info("Successfully imported extract_citations from app_final")
except ImportError:
    logger.error("Error importing extract_citations. Cannot proceed.")
    sys.exit(1)

# Initialize the verifier with API keys from config.json
api_keys = {}
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        api_keys["courtlistener"] = config.get("courtlistener_api_key")
        logger.info(
            f"Loaded CourtListener API key from config.json: {api_keys['courtlistener'][:5]}..."
        )
except Exception as e:
    logger.warning(f"Error loading API keys from config.json: {e}")

# Initialize the multi-source verifier
multi_source_verifier = MultiSourceVerifier(api_keys)

# Constants
BRIEFS_DIR = "wa_briefs"
PROCESSED_BRIEFS_CACHE = "processed_wa_briefs.json"
OUTPUT_FILE = "unverified_wa_citations.json"
MAX_BRIEFS_PER_DIVISION = 5  # Reduced from 20 to 5
MAX_TOTAL_BRIEFS = 20  # Reduced from 100 to 20
DOWNLOAD_DELAY_MIN = 5.0  # Increased from 1.0 to 5.0
DOWNLOAD_DELAY_MAX = 10.0  # Increased from 3.0 to 10.0
WA_COURTS_BASE_URL = "https://www.courts.wa.gov"
COA_URL = f"{WA_COURTS_BASE_URL}/appellate_trial_courts/coa/"

# Create directories if they don't exist
if not os.path.exists(BRIEFS_DIR):
    os.makedirs(BRIEFS_DIR)
    logger.info(f"Created directory: {BRIEFS_DIR}")


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


def get_court_of_appeals_links():
    """Get links to Court of Appeals divisions."""
    logger.info(f"Getting Court of Appeals division links from {COA_URL}")

    try:
        # Add a delay before making the request
        time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))

        # Make the request
        response = requests.get(COA_URL)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find division links
        division_links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            text = link.get_text(strip=True)

            # Look for division links
            if href and (
                "division-i" in href.lower()
                or "division-ii" in href.lower()
                or "division-iii" in href.lower()
            ):
                full_url = urljoin(WA_COURTS_BASE_URL, href)
                division_links.append((text, full_url))

        logger.info(f"Found {len(division_links)} Court of Appeals divisions")
        return division_links

    except Exception as e:
        logger.error(f"Error getting Court of Appeals links: {e}")
        return []


def get_brief_links_from_division(division_url, max_briefs=MAX_BRIEFS_PER_DIVISION):
    """Get links to briefs from a Court of Appeals division."""
    logger.info(f"Getting brief links from {division_url}")

    try:
        # Add a delay before making the request
        time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))

        # Make the request
        response = requests.get(division_url)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find brief links
        brief_links = []
        for link in soup.find_all("a"):
            href = link.get("href")

            # Look for PDF links that might be briefs
            if (
                href
                and href.lower().endswith(".pdf")
                and (
                    "brief" in href.lower()
                    or "appellant" in href.lower()
                    or "respondent" in href.lower()
                )
            ):
                full_url = urljoin(WA_COURTS_BASE_URL, href)
                brief_links.append(full_url)

                if len(brief_links) >= max_briefs:
                    break

        logger.info(f"Found {len(brief_links)} brief links")
        return brief_links

    except Exception as e:
        logger.error(f"Error getting brief links from {division_url}: {e}")
        return []


def download_brief(brief_url):
    """Download a brief from a URL."""
    logger.info(f"Downloading brief from {brief_url}")

    try:
        # Create a filename from the URL
        filename = os.path.basename(brief_url)
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        # Create the full path
        brief_path = os.path.join(BRIEFS_DIR, filename)

        # Check if the file already exists
        if os.path.exists(brief_path):
            logger.info(f"Brief already exists at {brief_path}")
            return brief_path

        # Add a delay before making the request
        time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))

        # Download the brief
        response = requests.get(brief_url, stream=True)
        response.raise_for_status()

        # Save the brief
        with open(brief_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"Downloaded brief to {brief_path}")
        return brief_path

    except Exception as e:
        logger.error(f"Error downloading brief from {brief_url}: {e}")
        return None


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    logger.info(f"Extracting text from {pdf_path}")

    try:
        # Try to import PyPDF2
        try:
            import PyPDF2
        except ImportError:
            logger.error(
                "PyPDF2 not installed. Please install it with 'pip install PyPDF2'"
            )
            return ""

        # Extract text from the PDF
        text = ""
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"

        logger.info(f"Extracted {len(text)} characters of text from {pdf_path}")
        return text

    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return ""


def process_brief(brief_url, processed_briefs):
    """Process a brief to extract and verify citations."""
    try:
        # Download the brief
        brief_path = download_brief(brief_url)
        if not brief_path:
            logger.warning(f"Failed to download brief from {brief_url}")
            return []

        # Extract text from the PDF
        text = extract_text_from_pdf(brief_path)
        if not text:
            logger.warning(f"Failed to extract text from {brief_path}")
            return []

        # Extract citations from the text
        citations = extract_citations(text)
        logger.info(f"Extracted {len(citations)} citations from {brief_path}")

        # Verify each citation
        unverified_citations = []
        for citation in citations:
            # Skip citations that don't look like case citations
            if not re.search(r"\d+\s+\w+\.?\s+\d+", citation):
                continue

            # Try to verify the citation
            try:
                result = multi_source_verifier.verify_citation(citation)

                # If the citation is not verified, add it to the list
                if not result["found"]:
                    # Get some context for the citation
                    context_match = re.search(
                        r"(.{0,100}" + re.escape(citation) + r".{0,100})", text
                    )
                    context = context_match.group(1) if context_match else ""

                    unverified_citations.append(
                        {
                            "citation": citation,
                            "brief_url": brief_url,
                            "brief_path": brief_path,
                            "context": context,
                            "verification_result": result,
                        }
                    )
                    logger.info(f"Found unverified citation: {citation}")

            except Exception as e:
                logger.error(f"Error verifying citation {citation}: {e}")

        # Add the brief to the list of processed briefs
        processed_briefs.append(brief_url)
        save_processed_briefs(processed_briefs)

        logger.info(
            f"Found {len(unverified_citations)} unverified citations in {brief_path}"
        )
        return unverified_citations

    except Exception as e:
        logger.error(f"Error processing brief {brief_url}: {e}")
        return []


def save_unverified_citations(unverified_citations):
    """Save unverified citations to a JSON file."""
    try:
        # Load existing citation verification results
        citation_file = os.path.join(
            os.path.dirname(__file__), "citation_verification_results.json"
        )
        citation_data = {"newly_confirmed": [], "still_unconfirmed": []}

        if os.path.exists(citation_file):
            try:
                with open(citation_file, "r") as f:
                    citation_data = json.load(f)
            except:
                pass

        # Add unconfirmed citations
        for citation_info in unverified_citations:
            citation_data["still_unconfirmed"].append(
                {
                    "citation": citation_info["citation"],
                    "explanation": citation_info["verification_result"].get(
                        "explanation", "Citation could not be verified"
                    ),
                    "confidence": citation_info["verification_result"].get(
                        "confidence", 0.1
                    ),
                    "document": os.path.basename(citation_info["brief_path"]),
                }
            )

        # Write updated data
        with open(citation_file, "w") as f:
            json.dump(citation_data, f, indent=2)

        # Also save the full unverified citations data
        with open(OUTPUT_FILE, "w") as f:
            json.dump(unverified_citations, f, indent=2)

        logger.info(
            f"Saved {len(unverified_citations)} unverified citations to {citation_file} and {OUTPUT_FILE}"
        )

    except Exception as e:
        logger.error(f"Error saving unverified citations: {e}")


def main():
    """Main function to process briefs and extract unverified citations."""
    logger.info(
        "Starting extraction of unverified citations from Washington Court briefs"
    )

    # Load processed briefs
    processed_briefs = load_processed_briefs()
    logger.info(f"Loaded {len(processed_briefs)} previously processed briefs")

    # Get Court of Appeals division links
    division_links = get_court_of_appeals_links()

    # Process each division
    all_unverified_citations = []
    total_briefs_processed = 0

    for division_name, division_url in division_links:
        logger.info(f"Processing division: {division_name} at {division_url}")

        # Get brief links from division
        brief_links = get_brief_links_from_division(
            division_url, max_briefs=MAX_BRIEFS_PER_DIVISION
        )

        # Filter out already processed briefs
        new_briefs = [brief for brief in brief_links if brief not in processed_briefs]
        logger.info(f"Found {len(new_briefs)} new briefs to process in {division_name}")

        # Process each brief
        for i, brief_url in enumerate(new_briefs):
            logger.info(
                f"Processing brief {i+1}/{len(new_briefs)} from {division_name}: {brief_url}"
            )
            unverified_citations = process_brief(brief_url, processed_briefs)
            all_unverified_citations.extend(unverified_citations)
            total_briefs_processed += 1

            # Save progress periodically
            if (i + 1) % 2 == 0 or i == len(new_briefs) - 1:
                save_unverified_citations(all_unverified_citations)

            # Add a small delay to avoid overwhelming the server
            time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))

            # Stop after processing MAX_TOTAL_BRIEFS briefs total
            if total_briefs_processed >= MAX_TOTAL_BRIEFS:
                logger.info(
                    f"Reached limit of {MAX_TOTAL_BRIEFS} briefs processed. Stopping."
                )
                break

        # Stop after processing MAX_TOTAL_BRIEFS briefs total
        if total_briefs_processed >= MAX_TOTAL_BRIEFS:
            break

    # Save final results
    save_unverified_citations(all_unverified_citations)

    logger.info("Finished extracting unverified citations from briefs")
    logger.info(
        f"Found {len(all_unverified_citations)} unverified citations in {total_briefs_processed} briefs"
    )


if __name__ == "__main__":
    main()
