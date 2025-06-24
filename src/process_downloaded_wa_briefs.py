"""
Process Downloaded Washington Court Briefs

This script processes the briefs downloaded from the Washington Courts website,
extracts citations, verifies them, and adds them to the CaseStrainer database.
"""

import os
import json
import sqlite3
import re
import logging
import time
import random
import requests

import PyPDF2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("wa_briefs_processing.log"), logging.StreamHandler()],
)
logger = logging.getLogger("wa_briefs_processor")

# Updated: Use the unified verify_citation from enhanced_multi_source_verifier
from src.enhanced_multi_source_verifier import verify_citation

# Constants
BRIEFS_DIR = "wa_briefs"
PROCESSED_BRIEFS_CACHE = "processed_wa_briefs.json"
DATABASE_FILE = os.path.join(os.path.dirname(__file__), "citations.db")
MAX_BRIEFS_TO_PROCESS = 10  # Limit the number of briefs to process
PROCESS_DELAY_MIN = 2.0  # Minimum delay between processing briefs in seconds
PROCESS_DELAY_MAX = 5.0  # Maximum delay between processing briefs in seconds

# Citation patterns
CITATION_PATTERNS = [
    # U.S. Reports pattern (e.g., 347 U.S. 483)
    r"\b(\d{1,3})\s+U\.?\s?S\.?\s+(\d{1,4})\b",
    # Federal Reporter pattern (e.g., 531 F.3d 1114)
    r"\b(\d{1,3})\s+F\.?\s?(?:2d|3d)\.?\s+(\d{1,4})\b",
    # Washington Reporter pattern (e.g., 198 Wash.2d 492)
    r"\b(\d{1,3})\s+Wash\.?\s?(?:2d|App\.?)\.?\s+(\d{1,4})\b",
    # Pacific Reporter pattern (e.g., 432 P.2d 123)
    r"\b(\d{1,3})\s+P\.?\s?(?:2d|3d)\.?\s+(\d{1,4})\b",
    # Westlaw pattern (e.g., 2022 WL 12345678)
    r"\b(20\d{2})\s+WL\s+(\d{8})\b",
]


def init_db():
    """Initialize the database with the necessary tables if they don't exist."""
    if not os.path.exists(os.path.dirname(DATABASE_FILE)):
        os.makedirs(os.path.dirname(DATABASE_FILE))

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Create tables for citations
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS citations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        citation_text TEXT NOT NULL,
        case_name TEXT,
        confidence REAL,
        found BOOLEAN,
        explanation TEXT,
        source TEXT,
        source_document TEXT,
        url TEXT,
        context TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    conn.commit()
    conn.close()
    logger.info("Database initialized")


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
            json.dump(processed_briefs, f, indent=2)
        logger.info(
            f"Saved {len(processed_briefs)} processed briefs to {PROCESSED_BRIEFS_CACHE}"
        )
    except Exception as e:
        logger.error(f"Error saving processed briefs cache: {e}")


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    logger.info(f"Extracting text from {pdf_path}")

    try:
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


def extract_citations(text):
    """Extract citations from text using regular expressions."""
    logger.info(f"Extracting citations from text ({len(text)} characters)")

    citations = []
    for pattern in CITATION_PATTERNS:
        matches = re.finditer(pattern, text)
        for match in matches:
            citation_text = match.group(0)
            context_start = max(0, match.start() - 100)
            context_end = min(len(text), match.end() + 100)
            context = text[context_start:context_end].replace("\n", " ").strip()

            citations.append({"citation_text": citation_text, "context": context})

    # Remove duplicates while preserving order
    unique_citations = []
    seen = set()
    for citation in citations:
        if citation["citation_text"] not in seen:
            seen.add(citation["citation_text"])
            unique_citations.append(citation)

    logger.info(f"Extracted {len(unique_citations)} unique citations")
    return unique_citations


def save_citation_to_db(citation, source_document):
    """Save a processed citation to the database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Check if citation already exists
        cursor.execute(
            "SELECT id FROM citations WHERE citation_text = ?",
            (citation["citation_text"],),
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing citation
            cursor.execute(
                """
            UPDATE citations SET
                case_name = ?,
                confidence = ?,
                found = ?,
                explanation = ?,
                source = ?,
                source_document = ?,
                url = ?,
                context = ?,
                date_added = CURRENT_TIMESTAMP
            WHERE citation_text = ?
            """,
                (
                    citation.get("case_name", "Unknown"),
                    citation.get("confidence", 0.0),
                    citation.get("found", False),
                    citation.get("explanation", ""),
                    citation.get("source", "None"),
                    source_document,
                    citation.get("url", ""),
                    citation.get("context", ""),
                    citation["citation_text"],
                ),
            )
        else:
            # Insert new citation
            cursor.execute(
                """
            INSERT INTO citations (
                citation_text, case_name, confidence, found, explanation,
                source, source_document, url, context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    citation["citation_text"],
                    citation.get("case_name", "Unknown"),
                    citation.get("confidence", 0.0),
                    citation.get("found", False),
                    citation.get("explanation", ""),
                    citation.get("source", "None"),
                    source_document,
                    citation.get("url", ""),
                    citation.get("context", ""),
                ),
            )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving citation to database: {e}")
        return False


def update_citation_json_files(multitool_citations, unconfirmed_citations):
    """Update the citation verification results JSON files."""
    # Update citation_verification_results.json
    citation_file = os.path.join(
        os.path.dirname(__file__), "citation_verification_results.json"
    )
    citation_data = {"newly_confirmed": [], "still_unconfirmed": []}

    if os.path.exists(citation_file):
        try:
            with open(citation_file, "r") as f:
                citation_data = json.load(f)
        except Exception as e:
            print(f"Error reading citation_verification_results.json: {e}")

    # Add unconfirmed citations
    for citation in unconfirmed_citations:
        citation_data["still_unconfirmed"].append(
            {
                "citation": citation["citation_text"],
                "explanation": citation.get(
                    "explanation", "Citation could not be verified"
                ),
                "confidence": citation.get("confidence", 0.1),
                "document": citation.get("source_document", "Unknown"),
            }
        )

    # Write updated data
    with open(citation_file, "w") as f:
        json.dump(citation_data, f, indent=2)

    # Update database_verification_results.json
    database_file = os.path.join(
        os.path.dirname(__file__), "database_verification_results.json"
    )
    database_data = []

    if os.path.exists(database_file):
        try:
            with open(database_file, "r") as f:
                database_data = json.load(f)
        except Exception as e:
            print(f"Error reading database_verification_results.json: {e}")

    # Add multitool citations
    for citation in multitool_citations:
        database_data.append(
            {
                "citation": citation["citation_text"],
                "case_name": citation.get("case_name", "Unknown"),
                "confidence": citation.get("confidence", 0.7),
                "source": citation.get("source", "Alternative Source"),
                "url": citation.get("url", ""),
                "explanation": citation.get(
                    "explanation", "Citation verified with alternative source"
                ),
            }
        )

    # Write updated data
    with open(database_file, "w") as f:
        json.dump(database_data, f, indent=2)

    logger.info(f"Updated citation JSON files: {citation_file} and {database_file}")


def process_brief(brief_path):
    """Process a brief to extract and verify citations."""
    try:
        # Extract text from the brief
        brief_text = extract_text_from_pdf(brief_path)
        if not brief_text:
            logger.error(f"No text extracted from brief: {brief_path}")
            return None

        # --- NEW: Send text to CourtListener citation-lookup API ---
        api_key = COURTLISTENER_API_KEY if 'COURTLISTENER_API_KEY' in globals() else os.environ.get('COURTLISTENER_API_KEY')
        headers = {"Authorization": f"Token {api_key}"} if api_key else {}
        response = requests.post(
            "https://www.courtlistener.com/api/rest/v4/citation-lookup/",
            headers=headers,
            data={"text": brief_text}
        )
        try:
            citations = response.json()
        except Exception as e:
            logger.error(f"Error parsing CourtListener response: {e}")
            return None
        logger.info(f"CourtListener returned {len(citations)} citations.")

        # --- process citations as needed ...
        return citations

    except Exception as e:
        logger.error(f"Error processing brief {brief_path}: {e}")
        return None


def main():
    """Main function to process downloaded briefs."""
    logger.info("Starting processing of downloaded Washington Court briefs")

    # Initialize the database
    init_db()

    # Load processed briefs
    processed_briefs = load_processed_briefs()
    logger.info(f"Loaded {len(processed_briefs)} previously processed briefs")

    # Load briefs metadata
    metadata_path = os.path.join(BRIEFS_DIR, "briefs_metadata.json")
    briefs_to_process = []

    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                briefs_to_process = json.load(f)
            logger.info(f"Loaded metadata for {len(briefs_to_process)} briefs")
        except Exception as e:
            logger.error(f"Error loading briefs metadata: {e}")

    if not briefs_to_process:
        # If no metadata file, process all PDF files in the directory
        logger.info(
            f"No briefs metadata found, scanning {BRIEFS_DIR} directory for PDFs"
        )
        for filename in os.listdir(BRIEFS_DIR):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(BRIEFS_DIR, filename)
                briefs_to_process.append(
                    {
                        "path": file_path,
                        "url": "",
                        "title": filename,
                        "case_number": "Unknown",
                        "case_title": "Unknown",
                        "court_id": "Unknown",
                    }
                )

    # Filter out already processed briefs
    new_briefs = [
        brief for brief in briefs_to_process if brief["path"] not in processed_briefs
    ]
    logger.info(f"Found {len(new_briefs)} new briefs to process")

    # Limit the number of briefs to process
    if len(new_briefs) > MAX_BRIEFS_TO_PROCESS:
        logger.info(f"Limiting to {MAX_BRIEFS_TO_PROCESS} briefs")
        new_briefs = new_briefs[:MAX_BRIEFS_TO_PROCESS]

    # Process each brief
    all_multitool_citations = []
    all_unconfirmed_citations = []

    for i, brief in enumerate(new_briefs):
        logger.info(f"Processing brief {i+1}/{len(new_briefs)}: {brief['path']}")

        multitool_citations, unconfirmed_citations = process_brief(brief["path"])

        all_multitool_citations.extend(multitool_citations)
        all_unconfirmed_citations.extend(unconfirmed_citations)

        # Save progress periodically
        if (i + 1) % 2 == 0 or i == len(new_briefs) - 1:
            update_citation_json_files(
                all_multitool_citations, all_unconfirmed_citations
            )

        # Add a delay between briefs
        time.sleep(random.uniform(PROCESS_DELAY_MIN, PROCESS_DELAY_MAX))

    # Save final results
    update_citation_json_files(all_multitool_citations, all_unconfirmed_citations)

    logger.info("Finished processing downloaded Washington Court briefs")
    logger.info(
        f"Found {len(all_multitool_citations)} citations verified with multitool"
    )
    logger.info(f"Found {len(all_unconfirmed_citations)} unconfirmed citations")

    print("Processing complete!")
    print(f"Found {len(all_multitool_citations)} citations verified with multitool")
    print(f"Found {len(all_unconfirmed_citations)} unconfirmed citations")


if __name__ == "__main__":
    main()
