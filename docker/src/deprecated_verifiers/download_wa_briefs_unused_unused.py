"""
Washington State Court Briefs Downloader

This script downloads briefs from the Washington State Courts website
and saves them to a local directory for processing.
"""

import os
import requests
import time
import random
from bs4 import BeautifulSoup
import logging
import argparse
from tqdm import tqdm
import re
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("wa_briefs_download.log"), logging.StreamHandler()],
)
logger = logging.getLogger("wa_briefs_downloader")


# Create directories if they don't exist
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")


# Base URL for Washington State Courts
BASE_URL = "https://www.courts.wa.gov"
SEARCH_URL = f"{BASE_URL}/appellate_trial_courts/briefbank"

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def download_brief(url, save_path, filename=None):
    """Download a brief from the given URL and save it to the specified path."""
    try:
        # Add a random delay to avoid overloading the server
        time.sleep(random.uniform(1, 3))

        response = requests.get(url, headers=HEADERS, stream=True)
        response.raise_for_status()

        # If filename is not provided, extract it from the URL or Content-Disposition header
        if not filename:
            if "Content-Disposition" in response.headers:
                content_disposition = response.headers["Content-Disposition"]
                filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
                if filename_match:
                    filename = filename_match.group(1)

            if not filename:
                filename = url.split("/")[-1]
                if "?" in filename:
                    filename = filename.split("?")[0]

        # Ensure filename has a .pdf extension
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        file_path = os.path.join(save_path, filename)

        # Download the file with progress bar
        total_size = int(response.headers.get("content-length", 0))
        with open(file_path, "wb") as f, tqdm(
            desc=filename,
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

        logger.info(f"Downloaded: {filename}")
        return file_path
    except Exception as e:
        logger.error(f"Error downloading {url}: {str(e)}")
        return None


def search_briefs(query="", court="", case_type="", year="", max_results=10):
    """Search for briefs using the provided criteria."""
    try:
        # Construct search parameters
        params = {
            "query": query,
            "court": court,
            "case_type": case_type,
            "year": year,
        }

        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}

        logger.info(f"Searching with params: {params}")

        # Make the search request
        response = requests.get(SEARCH_URL, params=params, headers=HEADERS)
        response.raise_for_status()

        # Parse the HTML response
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all brief links
        results = []
        brief_links = soup.select(".brief-item a")

        for i, link in enumerate(brief_links):
            if i >= max_results:
                break

            href = link.get("href")
            title = link.get_text(strip=True)

            # Construct the full URL if it's a relative path
            if href and not href.startswith("http"):
                href = f"{BASE_URL}{href}"

            if href:
                results.append({"title": title, "url": href, "id": f"brief_{i+1}"})

        logger.info(f"Found {len(results)} briefs")
        return results
    except Exception as e:
        logger.error(f"Error searching briefs: {str(e)}")
        return []


def download_briefs(briefs, download_dir):
    """Download a list of briefs to the specified directory."""
    ensure_dir(download_dir)

    downloaded_briefs = []
    for brief in briefs:
        logger.info(f"Downloading brief: {brief['title']}")

        # Create a sanitized filename
        filename = re.sub(r"[^\w\-\.]", "_", brief["title"])
        filename = f"{brief['id']}_{filename}.pdf"

        # Download the brief
        file_path = download_brief(brief["url"], download_dir, filename)

        if file_path:
            brief["local_path"] = file_path
            downloaded_briefs.append(brief)

    # Save metadata about the downloaded briefs
    metadata_path = os.path.join(download_dir, "briefs_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(downloaded_briefs, f, indent=2)

    logger.info(
        f"Downloaded {len(downloaded_briefs)} briefs. Metadata saved to {metadata_path}"
    )
    return downloaded_briefs


def main():
    parser = argparse.ArgumentParser(
        description="Download Washington State Court Briefs"
    )
    parser.add_argument("--query", type=str, default="", help="Search query")
    parser.add_argument(
        "--court", type=str, default="", help="Court (e.g., 'supreme', 'appeals')"
    )
    parser.add_argument("--case_type", type=str, default="", help="Case type")
    parser.add_argument("--year", type=str, default="", help="Year")
    parser.add_argument(
        "--max_results",
        type=int,
        default=5,
        help="Maximum number of results to download",
    )
    parser.add_argument(
        "--download_dir",
        type=str,
        default="wa_briefs",
        help="Directory to save downloaded briefs",
    )

    args = parser.parse_args()

    # Search for briefs
    briefs = search_briefs(
        query=args.query,
        court=args.court,
        case_type=args.case_type,
        year=args.year,
        max_results=args.max_results,
    )

    if not briefs:
        logger.warning("No briefs found matching the criteria.")
        return

    # Download the briefs
    download_briefs(briefs, args.download_dir)


if __name__ == "__main__":
    main()
