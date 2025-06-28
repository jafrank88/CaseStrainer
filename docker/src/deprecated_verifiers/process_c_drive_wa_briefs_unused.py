"""
Process Washington Court Briefs from C Drive

This script processes the Washington Court briefs downloaded to C:\WA_Court_Briefs,
extracts citations, and adds them to the CaseStrainer database.
"""

import os
import json
import logging
import sqlite3
import PyPDF2
import re
import uuid
from datetime import datetime
import importlib.util

# Constants
USER_DOCS = os.path.join(os.path.expanduser("~"), "Documents")
BRIEFS_DIR = os.path.join(USER_DOCS, "WA_Court_Briefs")
METADATA_FILE = os.path.join(BRIEFS_DIR, "briefs_metadata.json")
EXTRACTED_DIR = os.path.join(BRIEFS_DIR, "extracted_text")
CITATIONS_FILE = os.path.join(BRIEFS_DIR, "unverified_wa_citations.json")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(USER_DOCS, "wa_briefs_processing.log")),
    ],
)
logger = logging.getLogger("wa_briefs_processor")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "citations.db")

# Create directories if they don't exist
if not os.path.exists(EXTRACTED_DIR):
    try:
        os.makedirs(EXTRACTED_DIR)
        logger.info(f"Created directory: {EXTRACTED_DIR}")
    except Exception as e:
        logger.error(f"Error creating directory {EXTRACTED_DIR}: {e}")
        try:
            import subprocess

            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"New-Item -ItemType Directory -Path '{EXTRACTED_DIR}' -Force",
                ],
                check=True,
            )
            logger.info(f"Created directory with elevated privileges: {EXTRACTED_DIR}")
        except Exception as e:
            logger.error(f"Error creating directory with elevated privileges: {e}")
            raise


def load_metadata():
    """Load metadata of downloaded briefs."""
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
    return []


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    logger.info(f"Extracting text from {pdf_path}")

    try:
        text = ""
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"

        # Generate a unique ID for the extracted text
        text_id = str(uuid.uuid4())

        # Save the extracted text to a file
        text_path = os.path.join(EXTRACTED_DIR, f"extracted_text_{text_id}.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text)

        logger.info(f"Extracted text saved to {text_path}")

        return {
            "text_id": text_id,
            "text_path": text_path,
            "page_count": len(pdf_reader.pages),
        }

    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {e}")
        return None


def extract_citations(text):
    """
    Extract citations from text using regular expressions.
    This is a basic implementation and may not catch all citation formats.
    """
    citations = []

    # Common citation patterns
    patterns = [
        # Washington Reports
        r"\d+\s+Wn\.\s*(?:App\.)?\s*\d+",
        r"\d+\s+Wash\.\s*(?:App\.)?\s*\d+",
        r"\d+\s+P\.\s*\d+",
        r"\d+\s+P\.\s*\d+d",
        r"\d+\s+P\.\s*\d+th",
        # Federal citations
        r"\d+\s+U\.S\.\s*\d+",
        r"\d+\s+S\.\s*Ct\.\s*\d+",
        r"\d+\s+L\.\s*Ed\.\s*\d+",
        r"\d+\s+L\.\s*Ed\.\s*2d\s*\d+",
        r"\d+\s+F\.\s*\d+",
        r"\d+\s+F\.\s*\d+d",
        r"\d+\s+F\.\s*\d+th",
        r"\d+\s+F\.\s*Supp\.\s*\d+",
        r"\d+\s+F\.\s*Supp\.\s*\d+d",
        # Case names with v.
        r"[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match not in citations:
                citations.append(match)

    return citations


def verify_citation(citation):
    """
    Verify a citation using the CaseStrainer verification system.
    This is a placeholder and should be replaced with actual verification logic.
    """
    # Import the verification module
    try:
        # Try to import the MultiSourceVerifier
        spec = importlib.util.spec_from_file_location(
            "multi_source_verifier",
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "fixed_multi_source_verifier.py",
            ),
        )
        verifier_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier_module)

        # Create a verifier instance
        verifier = verifier_module.MultiSourceVerifier()

        # Verify the citation
        result = verifier.verify_citation(citation)

        logger.info(f"Verified citation: {citation}")
        logger.info(f"Verification result: {result}")

        return result

    except Exception as e:
        logger.error(f"Error verifying citation {citation}: {e}")
        return {"verified": False, "error": str(e)}


def add_to_database(citation, source, verification_result):
    """Add a citation to the CaseStrainer database."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the citation already exists in the database
        cursor.execute("SELECT id FROM citations WHERE citation = ?", (citation,))
        existing = cursor.fetchone()

        if existing:
            # Update the existing citation
            cursor.execute(
                "UPDATE citations SET source = ?, verified = ?, verification_date = ? WHERE id = ?",
                (
                    source,
                    verification_result.get("verified", False),
                    datetime.now().isoformat(),
                    existing[0],
                ),
            )
            logger.info(f"Updated existing citation in database: {citation}")
        else:
            # Insert a new citation
            cursor.execute(
                "INSERT INTO citations (citation, source, verified, verification_date) VALUES (?, ?, ?, ?)",
                (
                    citation,
                    source,
                    verification_result.get("verified", False),
                    datetime.now().isoformat(),
                ),
            )
            logger.info(f"Added new citation to database: {citation}")

        # Commit the changes
        conn.commit()

        # Close the connection
        conn.close()

        return True

    except Exception as e:
        logger.error(f"Error adding citation to database: {e}")
        return False


def process_brief(brief_info):
    """Process a brief and extract citations."""
    logger.info(f"Processing brief: {brief_info.get('path')}")

    try:
        # Extract text from the PDF
        extraction_result = extract_text_from_pdf(brief_info.get("path"))

        if not extraction_result:
            logger.error(f"Failed to extract text from {brief_info.get('path')}")
            return None

        # Read the extracted text
        with open(extraction_result.get("text_path"), "r", encoding="utf-8") as f:
            text = f.read()

        # Extract citations from the text
        citations = extract_citations(text)

        logger.info(f"Found {len(citations)} citations in {brief_info.get('path')}")

        # Verify each citation
        verified_citations = []
        unverified_citations = []

        for citation in citations:
            # Verify the citation
            verification_result = verify_citation(citation)

            # Add the citation to the database
            source = f"{brief_info.get('court_id')} - {brief_info.get('case_number')} - {brief_info.get('brief_type')}"
            add_to_database(citation, source, verification_result)

            # Add the citation to the appropriate list
            if verification_result.get("verified", False):
                verified_citations.append(
                    {
                        "citation": citation,
                        "source": source,
                        "verification_result": verification_result,
                    }
                )
            else:
                unverified_citations.append(
                    {
                        "citation": citation,
                        "source": source,
                        "verification_result": verification_result,
                    }
                )

        logger.info(f"Verified {len(verified_citations)} citations")
        logger.info(f"Unverified {len(unverified_citations)} citations")

        return {
            "brief_info": brief_info,
            "extraction_result": extraction_result,
            "citations": {
                "total": len(citations),
                "verified": verified_citations,
                "unverified": unverified_citations,
            },
        }

    except Exception as e:
        logger.error(f"Error processing brief {brief_info.get('path')}: {e}")
        return None


def save_unverified_citations(unverified_citations):
    """Save unverified citations to a JSON file."""
    try:
        with open(CITATIONS_FILE, "w") as f:
            json.dump(unverified_citations, f, indent=2)

        logger.info(
            f"Saved {len(unverified_citations)} unverified citations to {CITATIONS_FILE}"
        )
        return True

    except Exception as e:
        logger.error(f"Error saving unverified citations: {e}")
        return False


def main():
    """Main function to process briefs."""
    logger.info("Starting processing of Washington Court briefs")

    # Load metadata of downloaded briefs
    metadata = load_metadata()
    logger.info(f"Loaded metadata for {len(metadata)} briefs")

    # Process each brief
    processed_briefs = []
    all_unverified_citations = []

    for brief_info in metadata:
        # Skip briefs that were not downloaded
        if not brief_info.get("downloaded", False):
            continue

        # Process the brief
        result = process_brief(brief_info)

        if result:
            processed_briefs.append(result)

            # Add unverified citations to the list
            all_unverified_citations.extend(
                result.get("citations", {}).get("unverified", [])
            )

    # Save unverified citations
    save_unverified_citations(all_unverified_citations)

    logger.info(f"Finished processing {len(processed_briefs)} briefs")
    logger.info(f"Found {len(all_unverified_citations)} unverified citations")
    logger.info(f"Unverified citations saved to {CITATIONS_FILE}")


if __name__ == "__main__":
    main()
