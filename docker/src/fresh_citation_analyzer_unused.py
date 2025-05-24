"""
Fresh Supreme Court Brief Citation Analyzer

This script downloads Supreme Court briefs from the Justice Department website,
extracts citations, verifies them, and records unverified citations with context.
It clears the processed briefs cache to ensure fresh downloads.
"""

import os
import sys
import json
import requests
import traceback
import time
import random
import re
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import PyPDF2

# Try to import eyecite for citation extraction
try:
    from eyecite import get_citations
    from eyecite.tokenizers import HyperscanTokenizer

    print("Successfully imported eyecite for citation extraction")
    USE_EYECITE = True
except ImportError:
    print(
        "Warning: eyecite not installed. Will use regex patterns for citation extraction."
    )
    USE_EYECITE = False

# Constants
BRIEFS_DIR = "downloaded_briefs"
PROCESSED_BRIEFS_CACHE = "fresh_processed_briefs.json"
BRIEFS_CSV = "fresh_supreme_court_briefs.csv"
UNVERIFIED_CITATIONS_FILE = "fresh_unverified_citations.json"
CONTEXT_CHARS = 200  # Number of characters to include before and after the citation
MAX_BRIEFS = 100  # Maximum number of briefs to download
BASE_URL = "https://www.justice.gov/osg/supreme-court-briefs"
SEARCH_URL = "https://www.justice.gov/osg/supreme-court-briefs?text=&sc_term=All&type=All&subject=All&order=field_date&sort=desc&page="

# Citation patterns for different formats
CITATION_PATTERNS = {
    "us_reports": r"(\d+)\s+U\.S\.\s+(\d+)\s*\(\d{4}\)",  # e.g., 410 U.S. 113 (1973)
    "federal_reporter": r"(\d+)\s+F\.(\d)d\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 123 F.3d 456 (9th Cir. 1997)
    "federal_supplement": r"(\d+)\s+F\.\s*Supp\.\s*(\d+)?\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 456 F. Supp. 2d 789 (S.D.N.Y. 2005)
    "state_reporter": r"(\d+)\s+([A-Za-z\.]+)\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 123 Cal. App. 4th 456 (2004)
    "regional_reporter": r"(\d+)\s+([A-Za-z\.]+)(\d+)?\s+(\d+)\s*\(.*?\d{4}\)",  # e.g., 456 N.E.2d 789 (N.Y. 1983)
    "supreme_court_reporter": r"(\d+)\s+S\.?\s?Ct\.?\s+(\d+)",
    "lawyers_edition": r"(\d+)\s+L\.?\s?Ed\.?\s?(\d+)d\s+(\d+)",
}

# Create directories if they don't exist
if not os.path.exists(BRIEFS_DIR):
    os.makedirs(BRIEFS_DIR)


def clear_processed_briefs():
    """Clear the processed briefs cache."""
    if os.path.exists(PROCESSED_BRIEFS_CACHE):
        os.remove(PROCESSED_BRIEFS_CACHE)
    print("Cleared processed briefs cache")
    return []


def save_processed_briefs(processed_briefs):
    """Save the list of processed briefs."""
    try:
        with open(PROCESSED_BRIEFS_CACHE, "w") as f:
            json.dump(processed_briefs, f)
    except Exception as e:
        print(f"Error saving processed briefs cache: {e}")


def get_brief_info(page=0, max_pages=10):
    """Get brief information from the Justice Department website."""
    print(f"Getting brief information from page {page}...")

    briefs_info = []

    try:
        # Set up user agent to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Make the request
        url = f"{SEARCH_URL}{page}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Error getting brief information: {response.status_code}")
            return briefs_info

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all table rows with brief information
        rows = soup.find_all("tr")

        for row in rows:
            # Skip header rows
            if row.find("th"):
                continue

            # Extract cells
            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            # Extract brief information
            try:
                docket_number = cells[1].text.strip() if len(cells) > 1 else "Unknown"
                caption = cells[2].text.strip() if len(cells) > 2 else "Unknown"
                brief_type = cells[3].text.strip() if len(cells) > 3 else "Unknown"
                filing_date = cells[4].text.strip() if len(cells) > 4 else "Unknown"

                # Find the PDF link
                pdf_link = None
                link_cell = cells[2] if len(cells) > 2 else None
                if link_cell:
                    pdf_a_tag = link_cell.find_next(
                        "a", href=lambda href: href and href.endswith("?inline")
                    )
                    if pdf_a_tag:
                        pdf_link = urljoin(BASE_URL, pdf_a_tag["href"])

                if pdf_link:
                    # Extract media ID from the URL for unique filename
                    parsed_url = urlparse(pdf_link)
                    path_parts = parsed_url.path.split("/")
                    media_id = path_parts[-2] if len(path_parts) > 2 else "unknown"

                    briefs_info.append(
                        {
                            "docket_number": docket_number,
                            "caption": caption,
                            "brief_type": brief_type,
                            "filing_date": filing_date,
                            "pdf_url": pdf_link,
                            "media_id": media_id,
                        }
                    )
            except Exception as e:
                print(f"Error extracting brief information: {e}")
                continue

        # If we need more briefs and haven't reached the max pages, get more
        if len(briefs_info) < MAX_BRIEFS and page < max_pages - 1:
            time.sleep(random.uniform(1, 3))  # Add a small delay
            briefs_info.extend(get_brief_info(page + 1, max_pages))

        return briefs_info

    except Exception as e:
        print(f"Error getting brief information: {e}")
        traceback.print_exc()
        return briefs_info


def download_brief(brief_info):
    """Download a brief from a URL."""
    pdf_url = brief_info["pdf_url"]
    print(f"Downloading brief: {brief_info['caption']} ({pdf_url})")

    try:
        # Set up user agent to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Make the request
        response = requests.get(pdf_url, headers=headers)

        if response.status_code != 200:
            print(f"Error downloading brief: {response.status_code}")
            return None

        # Generate a unique filename based on the media ID and caption
        safe_caption = "".join(
            c if c.isalnum() else "_" for c in brief_info["caption"][:30]
        )
        filename = f"{brief_info['media_id']}_{safe_caption}.pdf"
        filepath = os.path.join(BRIEFS_DIR, filename)

        # Save the brief
        with open(filepath, "wb") as f:
            f.write(response.content)

        print(f"Saved brief to {filepath}")

        # Update brief_info with local filepath
        brief_info["local_path"] = filepath
        return brief_info

    except Exception as e:
        print(f"Error downloading brief: {e}")
        traceback.print_exc()
        return None


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    print(f"Extracting text from PDF: {pdf_path}")

    try:
        text = ""
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"

        return text

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        traceback.print_exc()
        return ""


def extract_citations(text):
    """Extract citations from text."""
    print("Extracting citations from text...")

    if USE_EYECITE:
        try:
            # Use eyecite to extract citations
            citations = get_citations(text, tokenizer=HyperscanTokenizer())

            # Extract citation strings
            citation_strings = []
            for citation in citations:
                citation_strings.append(citation.corrected_citation())

            return citation_strings

        except Exception as e:
            print(f"Error extracting citations with eyecite: {e}")
            traceback.print_exc()

    # Fallback to regex patterns
    print("Using regex patterns to extract citations...")
    citations = []

    for pattern_name, pattern in CITATION_PATTERNS.items():
        matches = re.finditer(pattern, text)
        for match in matches:
            citation = match.group(0)
            if citation not in citations:
                citations.append(citation)

    return citations


def verify_citation(citation):
    """Verify a citation using CourtListener API."""
    print(f"Verifying citation: {citation}")

    # For simplicity, we'll just check if the citation exists in CourtListener
    try:
        # Set up user agent to avoid being blocked
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # Make the request to CourtListener
        url = f"https://www.courtlistener.com/api/rest/v3/search/?type=o&q={citation}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Error verifying citation: {response.status_code}")
            return False

        # Parse the response
        data = response.json()

        # Check if the citation was found
        if data.get("count", 0) > 0:
            print(f"Citation verified: {citation}")
            return True

        print(f"Citation not verified: {citation}")
        return False

    except Exception as e:
        print(f"Error verifying citation: {e}")
        traceback.print_exc()
        return False


def extract_citation_context(text, citation):
    """Extract the context around a citation."""
    print(f"Extracting context for citation: {citation}")

    try:
        # Find all occurrences of the citation in the text
        citation_positions = []
        for match in re.finditer(re.escape(citation), text):
            start_pos = match.start()
            end_pos = match.end()
            citation_positions.append((start_pos, end_pos))

        if not citation_positions:
            print(f"Citation not found in text: {citation}")
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
            full_context = context_before + citation + context_after

            contexts.append(
                {
                    "context_before": context_before,
                    "context_after": context_after,
                    "full_context": full_context,
                }
            )

        return contexts[0] if contexts else None

    except Exception as e:
        print(f"Error extracting context for citation: {e}")
        traceback.print_exc()
        return None


def save_unverified_citations(unverified_citations):
    """Save unverified citations to a JSON file."""
    print(f"Saving {len(unverified_citations)} unverified citations...")

    try:
        # Load existing unverified citations if the file exists
        existing_citations = []
        if os.path.exists(UNVERIFIED_CITATIONS_FILE):
            try:
                with open(UNVERIFIED_CITATIONS_FILE, "r") as f:
                    existing_citations = json.load(f)
            except Exception as e:
                print(f"Error loading existing unverified citations: {e}")

        # Add new unverified citations
        existing_citations.extend(unverified_citations)

        # Save the combined list
        with open(UNVERIFIED_CITATIONS_FILE, "w") as f:
            json.dump(existing_citations, f, indent=2)

        print(
            f"Saved {len(unverified_citations)} unverified citations to {UNVERIFIED_CITATIONS_FILE}"
        )

    except Exception as e:
        print(f"Error saving unverified citations: {e}")
        traceback.print_exc()


def create_briefs_csv(briefs_info):
    """Create a CSV file with brief information."""
    print(f"Creating CSV file with {len(briefs_info)} briefs...")

    try:
        with open(BRIEFS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Docket Number",
                    "Caption",
                    "Brief Type",
                    "Filing Date",
                    "PDF URL",
                    "Local Path",
                    "Analyzed",
                    "Unverified Citations",
                ]
            )

            # Write brief information
            for brief in briefs_info:
                writer.writerow(
                    [
                        brief.get("docket_number", ""),
                        brief.get("caption", ""),
                        brief.get("brief_type", ""),
                        brief.get("filing_date", ""),
                        brief.get("pdf_url", ""),
                        brief.get("local_path", ""),
                        brief.get("analyzed", "No"),
                        brief.get("unverified_citations", "0"),
                    ]
                )

        print(f"Created CSV file: {BRIEFS_CSV}")

    except Exception as e:
        print(f"Error creating CSV file: {e}")
        traceback.print_exc()


def update_briefs_csv(briefs_info):
    """Update the CSV file with brief information."""
    print(f"Updating CSV file with {len(briefs_info)} briefs...")

    try:
        with open(BRIEFS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Docket Number",
                    "Caption",
                    "Brief Type",
                    "Filing Date",
                    "PDF URL",
                    "Local Path",
                    "Analyzed",
                    "Unverified Citations",
                ]
            )

            # Write brief information
            for brief in briefs_info:
                writer.writerow(
                    [
                        brief.get("docket_number", ""),
                        brief.get("caption", ""),
                        brief.get("brief_type", ""),
                        brief.get("filing_date", ""),
                        brief.get("pdf_url", ""),
                        brief.get("local_path", ""),
                        brief.get("analyzed", "Yes"),
                        brief.get("unverified_citations", "0"),
                    ]
                )

        print(f"Updated CSV file: {BRIEFS_CSV}")

    except Exception as e:
        print(f"Error updating CSV file: {e}")
        traceback.print_exc()


def process_brief(brief_info):
    """Process a brief to extract and verify citations."""
    print(f"Processing brief: {brief_info['caption']}")

    try:
        # Extract text from the PDF
        text = extract_text_from_pdf(brief_info["local_path"])
        if not text:
            print(f"No text extracted from brief: {brief_info['local_path']}")
            return []

        # Extract citations from the text
        citations = extract_citations(text)
        if not citations:
            print(f"No citations found in brief: {brief_info['local_path']}")
            return []

        print(f"Found {len(citations)} citations in brief: {brief_info['caption']}")

        # Verify each citation
        unverified_citations = []
        for citation in citations:
            # Verify the citation
            verified = verify_citation(citation)

            # If the citation is not verified, add it to the list
            if not verified:
                # Extract context for the citation
                context = extract_citation_context(text, citation)

                if context:
                    unverified_citations.append(
                        {
                            "citation_text": citation,
                            "source_brief": brief_info["caption"],
                            "brief_url": brief_info["pdf_url"],
                            "context_before": context["context_before"],
                            "context_after": context["context_after"],
                            "full_context": context["full_context"],
                        }
                    )

        print(
            f"Found {len(unverified_citations)} unverified citations in brief: {brief_info['caption']}"
        )

        # Update brief information
        brief_info["analyzed"] = "Yes"
        brief_info["unverified_citations"] = str(len(unverified_citations))

        return unverified_citations

    except Exception as e:
        print(f"Error processing brief: {e}")
        traceback.print_exc()
        return []


def main():
    """Main function to download and process briefs."""
    print("Starting Fresh Supreme Court Brief Citation Analyzer...")

    # Clear the processed briefs cache
    processed_briefs = clear_processed_briefs()

    # Get brief information
    briefs_info = get_brief_info()
    print(f"Found {len(briefs_info)} briefs")

    # Limit to MAX_BRIEFS
    briefs_info = briefs_info[:MAX_BRIEFS]

    # Download and process each brief
    downloaded_briefs = []
    all_unverified_citations = []

    for i, brief_info in enumerate(briefs_info):
        if i >= MAX_BRIEFS:
            break

        print(f"Processing brief {i+1} of {min(len(briefs_info), MAX_BRIEFS)}")

        # Download the brief
        downloaded_brief = download_brief(brief_info)
        if downloaded_brief:
            downloaded_briefs.append(downloaded_brief)

            # Process the brief
            unverified_citations = process_brief(downloaded_brief)
            all_unverified_citations.extend(unverified_citations)

            # Save after each brief to avoid losing data
            save_unverified_citations(unverified_citations)

            # Mark as processed
            processed_briefs.append(brief_info["pdf_url"])
            save_processed_briefs(processed_briefs)

        # Add a small delay to avoid overwhelming the server
        time.sleep(random.uniform(1, 3))

    # Create/update CSV file with brief information
    update_briefs_csv(downloaded_briefs)

    print(f"Finished downloading and processing {len(downloaded_briefs)} briefs")
    print(f"Found {len(all_unverified_citations)} total unverified citations")
    print(f"Unverified citations saved to {UNVERIFIED_CITATIONS_FILE}")
    print(f"Brief information saved to {BRIEFS_CSV}")

    # Create a tab-formatted file for the Unconfirmed Citations tab
    create_unconfirmed_citations_tab(all_unverified_citations)


def create_unconfirmed_citations_tab(unverified_citations):
    """Create a tab-formatted file for the Unconfirmed Citations tab."""
    print("Creating Unconfirmed Citations tab file...")

    try:
        with open("Unconfirmed_Citations_Tab.txt", "w", encoding="utf-8") as f:
            f.write("Citation\tBrief URL\tContext\n")

            for citation in unverified_citations:
                citation_text = citation["citation_text"]
                brief_url = citation["brief_url"]
                context = citation["full_context"].replace("\n", " ").replace("\t", " ")

                f.write(f"{citation_text}\t{brief_url}\t{context}\n")

        print("Created Unconfirmed Citations tab file: Unconfirmed_Citations_Tab.txt")

    except Exception as e:
        print(f"Error creating Unconfirmed Citations tab file: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
