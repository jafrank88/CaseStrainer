"""
Washington Court Briefs Downloader from Specific URLs

This script downloads briefs from the Washington Courts website using the provided URLs,
and saves them to a local directory for processing.
"""

import os
import json
import requests
import re
import time
import random
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("wa_briefs_download.log"), logging.StreamHandler()],
)
logger = logging.getLogger("wa_briefs_downloader")

# Constants
BRIEFS_DIR = "wa_briefs"
PROCESSED_CASES_CACHE = "processed_wa_cases.json"
MAX_BRIEFS_PER_CASE = 2  # Limit briefs per case to avoid downloading too many
MAX_CASES_PER_COURT = 5  # Limit cases per court to avoid downloading too many
MAX_TOTAL_CASES = 15  # Limit total cases to avoid downloading too many
DOWNLOAD_DELAY_MIN = 10.0  # Minimum delay between downloads in seconds
DOWNLOAD_DELAY_MAX = 20.0  # Maximum delay between downloads in seconds
COURT_DELAY_MIN = 30.0  # Minimum delay between courts in seconds
COURT_DELAY_MAX = 60.0  # Maximum delay between courts in seconds
WA_COURTS_BASE_URL = "https://www.courts.wa.gov"

# Court URLs
COURT_URLS = [
    "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A01",
    "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A02",
    "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A03",
    "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A08",
]

# Create directories if they don't exist
if not os.path.exists(BRIEFS_DIR):
    os.makedirs(BRIEFS_DIR)
    logger.info(f"Created directory: {BRIEFS_DIR}")


def load_processed_cases():
    """Load the list of already processed cases."""
    if os.path.exists(PROCESSED_CASES_CACHE):
        try:
            with open(PROCESSED_CASES_CACHE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading processed cases cache: {e}")
    return []


def save_processed_cases(processed_cases):
    """Save the list of processed cases."""
    try:
        with open(PROCESSED_CASES_CACHE, "w") as f:
            json.dump(processed_cases, f, indent=2)
        logger.info(
            f"Saved {len(processed_cases)} processed cases to {PROCESSED_CASES_CACHE}"
        )
    except Exception as e:
        logger.error(f"Error saving processed cases cache: {e}")


def get_case_links(court_url, max_cases=MAX_CASES_PER_COURT):
    """Get links to cases from a court URL."""
    logger.info(f"Getting case links from {court_url}")

    try:
        # Add a delay before making the request
        time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))

        # Make the request
        response = requests.get(court_url)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find case links
        case_links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            text = link.get_text(strip=True)

            # Look for case links
            if href and "briefsByCaseNumber" in href:
                # Extract case number and docket ID
                parsed_url = urlparse(href)
                query_params = parse_qs(parsed_url.query)
                case_number = query_params.get("caseNumber", ["Unknown"])[0]
                docket_id = query_params.get("docketId", ["Unknown"])[0]

                full_url = urljoin(WA_COURTS_BASE_URL, href)
                case_links.append(
                    {
                        "url": full_url,
                        "case_number": case_number,
                        "docket_id": docket_id,
                        "title": text.strip() if text else f"Case {case_number}",
                    }
                )

                if len(case_links) >= max_cases:
                    break

        logger.info(f"Found {len(case_links)} case links")
        return case_links

    except Exception as e:
        logger.error(f"Error getting case links from {court_url}: {e}")
        return []


def get_brief_links(case_url, max_briefs=MAX_BRIEFS_PER_CASE):
    """Get links to briefs from a case URL."""
    logger.info(f"Getting brief links from {case_url}")

    try:
        # Add a delay before making the request
        time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))

        # Make the request
        response = requests.get(case_url)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find brief links
        brief_links = []
        for link in soup.find_all("a"):
            href = link.get("href")
            text = link.get_text(strip=True)

            # Look for PDF links that might be briefs
            if href and href.lower().endswith(".pdf"):
                full_url = urljoin(WA_COURTS_BASE_URL, href)
                brief_type = "Unknown"

                # Try to determine brief type from text or URL
                if text:
                    brief_type = text.strip()
                elif "appellant" in href.lower():
                    brief_type = "Appellant Brief"
                elif "respondent" in href.lower():
                    brief_type = "Respondent Brief"
                elif "reply" in href.lower():
                    brief_type = "Reply Brief"
                elif "amicus" in href.lower():
                    brief_type = "Amicus Brief"

                brief_links.append(
                    {
                        "url": full_url,
                        "title": brief_type,
                        "filename": os.path.basename(href),
                    }
                )

                if len(brief_links) >= max_briefs:
                    break

        logger.info(f"Found {len(brief_links)} brief links")
        return brief_links

    except Exception as e:
        logger.error(f"Error getting brief links from {case_url}: {e}")
        return []


def download_brief(brief_info, case_info, court_id):
    """Download a brief from a URL."""
    brief_url = brief_info["url"]
    logger.info(f"Downloading brief from {brief_url}")

    try:
        # Create a sanitized filename
        case_number = re.sub(r"[^\w\-\.]", "_", case_info["case_number"])
        brief_type = re.sub(r"[^\w\-\.]", "_", brief_info["title"])

        # Create a unique filename
        filename = f"{court_id}_{case_number}_{brief_type}.pdf"

        # Create the full path
        brief_path = os.path.join(BRIEFS_DIR, filename)

        # Check if the file already exists
        if os.path.exists(brief_path):
            logger.info(f"Brief already exists at {brief_path}")
            return {
                "path": brief_path,
                "url": brief_url,
                "title": brief_info["title"],
                "case_number": case_info["case_number"],
                "case_title": case_info["title"],
                "court_id": court_id,
                "downloaded": False,
            }

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
        return {
            "path": brief_path,
            "url": brief_url,
            "title": brief_info["title"],
            "case_number": case_info["case_number"],
            "case_title": case_info["title"],
            "court_id": court_id,
            "downloaded": True,
        }

    except Exception as e:
        logger.error(f"Error downloading brief from {brief_url}: {e}")
        return None


def process_court(court_url, processed_cases, downloaded_briefs, total_cases_processed):
    """Process a court URL to download briefs."""
    # Extract court ID from URL
    parsed_url = urlparse(court_url)
    query_params = parse_qs(parsed_url.query)
    court_id = query_params.get("courtId", ["Unknown"])[0]

    logger.info(f"Processing court {court_id} at {court_url}")

    # Get case links
    case_links = get_case_links(court_url, max_cases=MAX_CASES_PER_COURT)

    # Filter out already processed cases
    new_cases = [case for case in case_links if case["url"] not in processed_cases]
    logger.info(f"Found {len(new_cases)} new cases to process in court {court_id}")

    # Process each case
    cases_processed = 0
    for case in new_cases:
        logger.info(f"Processing case {case['case_number']}: {case['title']}")

        # Get brief links
        brief_links = get_brief_links(case["url"], max_briefs=MAX_BRIEFS_PER_CASE)

        # Download each brief
        for brief in brief_links:
            brief_info = download_brief(brief, case, court_id)
            if brief_info:
                downloaded_briefs.append(brief_info)

        # Add the case to the list of processed cases
        processed_cases.append(case["url"])
        save_processed_cases(processed_cases)

        # Save downloaded briefs metadata
        save_downloaded_briefs(downloaded_briefs)

        cases_processed += 1
        total_cases_processed += 1

        # Stop after processing MAX_TOTAL_CASES cases total
        if total_cases_processed >= MAX_TOTAL_CASES:
            logger.info(
                f"Reached limit of {MAX_TOTAL_CASES} cases processed. Stopping."
            )
            return total_cases_processed

        # Add a delay between cases
        time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))

    return total_cases_processed


def save_downloaded_briefs(downloaded_briefs):
    """Save metadata about downloaded briefs."""
    try:
        metadata_path = os.path.join(BRIEFS_DIR, "briefs_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(downloaded_briefs, f, indent=2)
        logger.info(
            f"Saved metadata for {len(downloaded_briefs)} briefs to {metadata_path}"
        )
    except Exception as e:
        logger.error(f"Error saving briefs metadata: {e}")


def main():
    """Main function to download briefs from Washington Courts."""
    logger.info("Starting download of Washington Court briefs")

    # Load processed cases
    processed_cases = load_processed_cases()
    logger.info(f"Loaded {len(processed_cases)} previously processed cases")

    # Initialize downloaded briefs list
    downloaded_briefs = []

    # Load existing briefs metadata if it exists
    metadata_path = os.path.join(BRIEFS_DIR, "briefs_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                downloaded_briefs = json.load(f)
            logger.info(
                f"Loaded metadata for {len(downloaded_briefs)} previously downloaded briefs"
            )
        except Exception as e:
            logger.error(f"Error loading briefs metadata: {e}")

    # Process each court
    total_cases_processed = 0
    for court_url in COURT_URLS:
        total_cases_processed = process_court(
            court_url, processed_cases, downloaded_briefs, total_cases_processed
        )

        # Stop after processing MAX_TOTAL_CASES cases total
        if total_cases_processed >= MAX_TOTAL_CASES:
            break

        # Add a delay between courts
        time.sleep(random.uniform(COURT_DELAY_MIN, COURT_DELAY_MAX))

    # Save final results
    save_processed_cases(processed_cases)
    save_downloaded_briefs(downloaded_briefs)

    logger.info("Finished downloading Washington Court briefs")

    # Count newly downloaded briefs
    newly_downloaded = sum(
        1 for brief in downloaded_briefs if brief.get("downloaded", False)
    )
    logger.info(
        f"Downloaded {newly_downloaded} new briefs from {total_cases_processed} cases"
    )
    logger.info(f"Total briefs in collection: {len(downloaded_briefs)}")


if __name__ == "__main__":
    main()
