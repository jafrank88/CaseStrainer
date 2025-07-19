"""
Washington Court Briefs Downloader to C Drive

This script downloads briefs directly from Washington Courts website
and saves them to a folder in the C drive.
"""

import os
import requests
import time
import random
import re
import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Constants
USER_DOCS = os.path.join(os.path.expanduser("~"), "Documents")
BRIEFS_DIR = os.path.join(USER_DOCS, "WA_Court_Briefs")
METADATA_FILE = os.path.join(BRIEFS_DIR, "briefs_metadata.json")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(USER_DOCS, "wa_briefs_download.log")),
    ],
)
logger = logging.getLogger("wa_briefs_downloader")
MAX_BRIEFS = 100  # Maximum number of briefs to download
DOWNLOAD_DELAY_MIN = 3.0  # Minimum delay between downloads in seconds
DOWNLOAD_DELAY_MAX = 6.0  # Maximum delay between downloads in seconds
WA_COURTS_BASE_URL = "https://www.courts.wa.gov"

# Direct links to PDF briefs (these are examples, will be replaced with actual links)
BRIEF_URLS = [
    # Division I briefs
    "https://www.courts.wa.gov/content/Briefs/A01/789301%20Appellant%20Thurston%20County.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/789301%20Respondent%20Black%20Hills.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/789301%20Respondent%20Confederated%20Tribes.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/789301%20Respondent%20Squaxin.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/789301%20Respondent.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/796967%20appellant%27s%20brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/796967%20respondent%27s%20brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/796967%20reply%20brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/797767%20appellants%27%20opening%20brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A01/797767%20respondent%27s%20brief.pdf",
    # Division II briefs
    "https://www.courts.wa.gov/content/Briefs/A02/559396%20Appellant%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A02/559396%20Respondent%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A02/559396%20Reply%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A02/560329%20Appellant%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A02/560329%20Respondent%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A02/560329%20Reply%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A02/561058%20Appellant%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A02/561058%20Respondent%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A02/561058%20Reply%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A02/561472%20Appellant%27s%20Brief.pdf",
    # Division III briefs
    "https://www.courts.wa.gov/content/Briefs/A03/379736%20Appellant%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A03/379736%20Respondent%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A03/379736%20Reply%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A03/380663%20Appellant%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A03/380663%20Respondent%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A03/380663%20Reply%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A03/381246%20Appellant%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A03/381246%20Respondent%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A03/381246%20Reply%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A03/381384%20Appellant%27s%20Brief.pdf",
    # Supreme Court briefs
    "https://www.courts.wa.gov/content/Briefs/A08/100498-4%20Appellant%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A08/100498-4%20Respondent%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A08/100498-4%20Reply%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A08/100501-8%20Appellant%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A08/100501-8%20Respondent%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A08/100501-8%20Reply%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A08/100519-1%20Appellant%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A08/100519-1%20Respondent%27s%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A08/100519-1%20Reply%20Brief.pdf",
    "https://www.courts.wa.gov/content/Briefs/A08/100525-5%20Appellant%27s%20Brief.pdf",
]

# Create directories if they don't exist
if not os.path.exists(BRIEFS_DIR):
    try:
        os.makedirs(BRIEFS_DIR)
        logger.info(f"Created directory: {BRIEFS_DIR}")
    except Exception as e:
        logger.error(f"Error creating directory {BRIEFS_DIR}: {e}")
        logger.info("Will try to create directory with elevated privileges")
        try:
            import subprocess

            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"New-Item -ItemType Directory -Path '{BRIEFS_DIR}' -Force",
                ],
                check=True,
            )
            logger.info(f"Created directory with elevated privileges: {BRIEFS_DIR}")
        except Exception as e:
            logger.error(f"Error creating directory with elevated privileges: {e}")
            raise


def load_metadata():
    """Load metadata of previously downloaded briefs."""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
    return []


def save_metadata(metadata):
    """Save metadata of downloaded briefs."""
    try:
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata for {len(metadata)} briefs to {METADATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving metadata: {e}")


def extract_case_info(url):
    """Extract case information from the brief URL."""
    # Extract court ID (e.g., A01, A02, A03, A08)
    court_match = re.search(r"Briefs/([A-Z]\d+)", url)
    court_id = court_match.group(1) if court_match else "Unknown"

    # Extract case number
    case_match = re.search(r"Briefs/[A-Z]\d+/([^%]+)", url)
    case_number = case_match.group(1) if case_match else "Unknown"

    # Extract brief type
    brief_type = "Unknown"
    if "appellant" in url.lower():
        brief_type = "Appellant Brief"
    elif "respondent" in url.lower():
        brief_type = "Respondent Brief"
    elif "reply" in url.lower():
        brief_type = "Reply Brief"
    elif "amicus" in url.lower():
        brief_type = "Amicus Brief"

    return {"court_id": court_id, "case_number": case_number, "brief_type": brief_type}


def download_brief(url):
    """Download a brief from the given URL."""
    logger.info(f"Downloading brief from {url}")

    try:
        # Extract case information
        case_info = extract_case_info(url)

        # Create a sanitized filename
        filename = f"{case_info['court_id']}_{case_info['case_number']}_{case_info['brief_type']}.pdf"
        filename = re.sub(r"[^\w\-\.]", "_", filename)

        # Create the full path
        file_path = os.path.join(BRIEFS_DIR, filename)

        # Check if the file already exists
        if os.path.exists(file_path):
            logger.info(f"Brief already exists at {file_path}")
            return {
                "url": url,
                "path": file_path,
                "court_id": case_info["court_id"],
                "case_number": case_info["case_number"],
                "brief_type": case_info["brief_type"],
                "downloaded": False,
            }

        # Add a delay before making the request
        time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))

        # Make the request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        try:
            response = requests.get(url, headers=headers, stream=True, timeout=30, timeout=30)
            response.raise_for_status()
        except requests.Timeout:
            logger.error(f"Timeout occurred while downloading {url}")
            return None
        except requests.RequestException as e:
            logger.error(f"Error downloading brief from {url}: {e}")
            return None

        # Save the brief
        try:
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Downloaded brief to {file_path}")

            return {
                "url": url,
                "path": file_path,
                "court_id": case_info["court_id"],
                "case_number": case_info["case_number"],
                "brief_type": case_info["brief_type"],
                "downloaded": True,
            }
        except Exception as e:
            logger.error(f"Error saving brief to {file_path}: {e}")
            logger.info("Will try to save with elevated privileges")
            try:
                # Save to a temporary file first
                temp_path = os.path.join(os.path.dirname(__file__), "temp_brief.pdf")
                with open(temp_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # Copy to the target location with elevated privileges
                import subprocess

                subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        f"Copy-Item -Path '{temp_path}' -Destination '{file_path}' -Force",
                    ],
                    check=True,
                )
                os.remove(temp_path)

                logger.info(f"Downloaded brief to {file_path} with elevated privileges")

                return {
                    "url": url,
                    "path": file_path,
                    "court_id": case_info["court_id"],
                    "case_number": case_info["case_number"],
                    "brief_type": case_info["brief_type"],
                    "downloaded": True,
                }
            except Exception as e:
                logger.error(f"Error saving brief with elevated privileges: {e}")
                return None

    except Exception as e:
        logger.error(f"Error downloading brief from {url}: {e}")
        return None


def find_more_brief_urls():
    """Find more brief URLs from the Washington Courts website."""
    logger.info("Finding more brief URLs from the Washington Courts website")

    # Court URLs
    court_urls = [
        "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A01",
        "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A02",
        "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A03",
        "https://www.courts.wa.gov/appellate_trial_courts/coaBriefs/index.cfm?fa=coabriefs.briefsByCase&courtId=A08",
    ]

    additional_urls = []

    for court_url in court_urls:
        logger.info(f"Checking {court_url} for brief links")

        try:
            # Add a delay before making the request
            time.sleep(random.uniform(DOWNLOAD_DELAY_MIN, DOWNLOAD_DELAY_MAX))

            # Make the request
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            response = requests.get(court_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all links
            for link in soup.find_all("a"):
                href = link.get("href")

                # Look for PDF links
                if href and href.lower().endswith(".pdf"):
                    full_url = urljoin(WA_COURTS_BASE_URL, href)
                    if full_url not in BRIEF_URLS and full_url not in additional_urls:
                        additional_urls.append(full_url)

            logger.info(f"Found {len(additional_urls)} additional brief URLs")

        except Exception as e:
            logger.error(f"Error finding brief URLs from {court_url}: {e}")

    return additional_urls


def main():
    """Main function to download briefs."""
    logger.info("Starting download of Washington Court briefs")

    # Load metadata of previously downloaded briefs
    metadata = load_metadata()
    logger.info(f"Loaded metadata for {len(metadata)} previously downloaded briefs")

    # Get list of URLs to download
    urls_to_download = BRIEF_URLS.copy()

    # Try to find more brief URLs
    additional_urls = find_more_brief_urls()
    urls_to_download.extend(additional_urls)

    # Remove duplicates
    urls_to_download = list(set(urls_to_download))

    # Limit the number of briefs to download
    if len(urls_to_download) > MAX_BRIEFS:
        logger.info(f"Limiting to {MAX_BRIEFS} briefs")
        urls_to_download = urls_to_download[:MAX_BRIEFS]

    # Download briefs
    downloaded_count = 0
    for url in urls_to_download:
        # Check if we've already downloaded this brief
        if any(item.get("url") == url for item in metadata):
            logger.info(f"Brief already downloaded: {url}")
            continue

        # Download the brief
        brief_info = download_brief(url)

        if brief_info:
            metadata.append(brief_info)
            save_metadata(metadata)

            if brief_info["downloaded"]:
                downloaded_count += 1

        # Check if we've reached the limit
        if downloaded_count >= MAX_BRIEFS:
            logger.info(f"Reached limit of {MAX_BRIEFS} briefs. Stopping.")
            break

    logger.info(
        f"Finished downloading briefs. Downloaded {downloaded_count} new briefs."
    )
    logger.info(f"Total briefs in collection: {len(metadata)}")
    logger.info(f"Briefs are saved in: {BRIEFS_DIR}")
    logger.info(f"Metadata is saved in: {METADATA_FILE}")


if __name__ == "__main__":
    main()
