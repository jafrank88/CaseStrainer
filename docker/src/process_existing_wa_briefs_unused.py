"""
Process Existing Washington Court Briefs

This script processes the Washington Court briefs that were previously downloaded
to D:\CaseStrainer\downloaded_briefs, extracts citations, and adds them to the CaseStrainer database.
"""

import os
import sys
import json
import logging
import sqlite3
import PyPDF2
import re
import uuid
import shutil
from datetime import datetime
from pathlib import Path
import importlib.util
from tqdm import tqdm

# Constants
USER_DOCS = os.path.join(os.path.expanduser("~"), "Documents")
BRIEFS_DIR = "D:\\CaseStrainer\\downloaded_briefs"
RESULTS_DIR = os.path.join(USER_DOCS, "WA_Briefs_Results")
EXTRACTED_DIR = os.path.join(RESULTS_DIR, "extracted_text")
CITATIONS_FILE = os.path.join(RESULTS_DIR, "unverified_wa_citations.json")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "citations.db")
FILE_LINKS_DIR = os.path.join(RESULTS_DIR, "file_links")
CONTEXT_LENGTH = 200  # Number of characters to extract before and after a citation

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

# Create directories if they don't exist
for directory in [RESULTS_DIR, EXTRACTED_DIR, FILE_LINKS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")


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


def extract_citations_with_context(text):
    """
    Extract citations from text using regular expressions and include context around each citation.
    Returns a list of dictionaries with citation text and surrounding context.
    """
    citation_data = []

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
        for match in re.finditer(pattern, text):
            citation = match.group(0)
            start_pos = max(0, match.start() - CONTEXT_LENGTH)
            end_pos = min(len(text), match.end() + CONTEXT_LENGTH)
            context = text[start_pos:end_pos]

            # Check if this citation is already in our list
            existing = next(
                (item for item in citation_data if item["citation"] == citation), None
            )
            if not existing:
                citation_data.append(
                    {
                        "citation": citation,
                        "context": context,
                        "positions": [{"start": match.start(), "end": match.end()}],
                    }
                )
            else:
                # Add this position to the existing citation
                existing["positions"].append(
                    {"start": match.start(), "end": match.end()}
                )

    return citation_data


def verify_citation(citation):
    """
    Verify a citation using the CaseStrainer verification system.
    First tries to use the enhanced multi-source verifier, then falls back to the original.
    """
    try:
        # First try to import the EnhancedMultiSourceVerifier
        try:
            spec = importlib.util.spec_from_file_location(
                "enhanced_multi_source_verifier",
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "enhanced_multi_source_verifier.py",
                ),
            )
            verifier_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(verifier_module)

            # Create a verifier instance
            verifier = verifier_module.EnhancedMultiSourceVerifier()
            logger.info("Using EnhancedMultiSourceVerifier for citation verification")
        except Exception as e:
            logger.warning(f"Could not import EnhancedMultiSourceVerifier: {e}")
            logger.warning("Falling back to original MultiSourceVerifier")

            # Fall back to the original MultiSourceVerifier
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


def add_to_database(citation_data, source, verification_result, file_link=None):
    """Add a citation to the CaseStrainer database with context and file link."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Extract citation components from verification result if available
        components = verification_result.get("components", {})
        volume = components.get("volume", "")
        reporter = components.get("reporter", "")
        page = components.get("page", "")
        court = components.get("court", "")
        year = components.get("year", "")

        # Check if the citation already exists in the database
        cursor.execute(
            "SELECT id FROM citations WHERE citation_text = ?",
            (citation_data["citation"],),
        )
        existing = cursor.fetchone()

        if existing:
            # Update the existing citation
            cursor.execute(
                """UPDATE citations SET 
                   source = ?, 
                   source_document = ?,
                   found = ?, 
                   explanation = ?,
                   context = ?,
                   file_link = ?,
                   volume = ?,
                   reporter = ?,
                   page = ?,
                   court = ?,
                   year = ?,
                   date_added = ? 
                   WHERE id = ?""",
                (
                    source,
                    source,
                    verification_result.get("verified", False),
                    (
                        verification_result.get("verified_by", "")
                        if verification_result.get("verified", False)
                        else verification_result.get("error", "")
                    ),
                    citation_data.get("context", ""),
                    file_link,
                    volume,
                    reporter,
                    page,
                    court,
                    year,
                    datetime.now().isoformat(),
                    existing[0],
                ),
            )
            logger.info(
                f"Updated existing citation in database: {citation_data['citation']}"
            )
        else:
            # Insert a new citation
            cursor.execute(
                """INSERT INTO citations 
                   (citation_text, source, source_document, found, explanation, context, file_link, 
                    volume, reporter, page, court, year, date_added) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    citation_data["citation"],
                    source,
                    source,
                    verification_result.get("verified", False),
                    (
                        verification_result.get("verified_by", "")
                        if verification_result.get("verified", False)
                        else verification_result.get("error", "")
                    ),
                    citation_data.get("context", ""),
                    file_link,
                    volume,
                    reporter,
                    page,
                    court,
                    year,
                    datetime.now().isoformat(),
                ),
            )
            logger.info(f"Added new citation to database: {citation_data['citation']}")

        # Commit the changes
        conn.commit()

        # Close the connection
        conn.close()

        return True

    except Exception as e:
        logger.error(f"Error adding citation to database: {e}")
        return False


def create_file_link(brief_path):
    """Create a link to the brief file by copying it to the file_links directory."""
    try:
        # Generate a unique filename for the copied file
        file_name = os.path.basename(brief_path)
        unique_id = str(uuid.uuid4())[:8]
        new_file_name = f"{unique_id}_{file_name}"
        new_file_path = os.path.join(FILE_LINKS_DIR, new_file_name)

        # Copy the file
        shutil.copy2(brief_path, new_file_path)
        logger.info(f"Created file link: {new_file_path}")

        # Return the relative path to the file
        return os.path.join("WA_Briefs_Results", "file_links", new_file_name)

    except Exception as e:
        logger.error(f"Error creating file link for {brief_path}: {e}")
        return None


def process_brief(brief_path):
    """Process a brief and extract citations."""
    logger.info(f"Processing brief: {brief_path}")

    try:
        # Extract court and case information from the file path
        path_parts = brief_path.split(os.sep)
        court_id = path_parts[-2] if len(path_parts) > 1 else "Unknown"
        file_name = os.path.basename(brief_path)

        # Create a file link for the brief
        file_link = create_file_link(brief_path)

        # Extract text from the PDF
        extraction_result = extract_text_from_pdf(brief_path)

        if not extraction_result:
            logger.error(f"Failed to extract text from {brief_path}")
            return None

        # Extract citations with context from the text
        with open(extraction_result["text_path"], "r", encoding="utf-8") as f:
            text = f.read()

        citation_data = extract_citations_with_context(text)
        logger.info(f"Extracted {len(citation_data)} citations from {brief_path}")

        # Verify each citation
        verified_citations = []
        unverified_citations = []

        for citation_item in citation_data:
            verification_result = verify_citation(citation_item["citation"])

            # Add the citation to the database with context and file link
            add_to_database(
                citation_item, f"WA Brief: {file_name}", verification_result, file_link
            )

            if verification_result.get("verified", False):
                verified_citations.append(
                    {
                        "citation": citation_item["citation"],
                        "context": citation_item["context"],
                        "source": f"WA Brief: {file_name}",
                        "file_link": file_link,
                        "verification_result": verification_result,
                    }
                )
            else:
                unverified_citations.append(
                    {
                        "citation": citation_item["citation"],
                        "context": citation_item["context"],
                        "source": f"WA Brief: {file_name}",
                        "file_link": file_link,
                        "verification_result": verification_result,
                    }
                )

        logger.info(f"Verified {len(verified_citations)} citations")
        logger.info(f"Unverified {len(unverified_citations)} citations")

        return {
            "brief_path": brief_path,
            "extraction_result": extraction_result,
            "citations": {
                "total": len(citation_data),
                "verified": verified_citations,
                "unverified": unverified_citations,
            },
        }

    except Exception as e:
        logger.error(f"Error processing brief {brief_path}: {e}")
        return None


def save_unverified_citations(unverified_citations):
    """Save unverified citations to a JSON file."""
    try:
        with open(CITATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(unverified_citations, f, indent=4)
        logger.info(
            f"Saved {len(unverified_citations)} unverified citations to {CITATIONS_FILE}"
        )

        # Also save a report with statistics
        report_path = os.path.join(RESULTS_DIR, "citation_processing_report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"Citation Processing Report\n")
            f.write(f"=========================\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total unverified citations: {len(unverified_citations)}\n\n")

            # Group by verification error
            error_counts = {}
            for citation in unverified_citations:
                error = citation["verification_result"].get("error", "Unknown error")
                error_counts[error] = error_counts.get(error, 0) + 1

            f.write(f"Error breakdown:\n")
            for error, count in error_counts.items():
                f.write(f"  - {error}: {count}\n")

        logger.info(f"Saved citation processing report to {report_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving unverified citations: {e}")
        return False


def find_briefs():
    """Find all PDF briefs in the BRIEFS_DIR directory."""
    briefs = []

    for root, dirs, files in os.walk(BRIEFS_DIR):
        for file in files:
            if file.lower().endswith(".pdf"):
                brief_path = os.path.join(root, file)
                briefs.append(brief_path)

    return briefs


def main():
    """Main function to process briefs."""
    logger.info(
        "Starting Washington briefs processing with enhanced citation validation"
    )

    # Check if database has the necessary columns for enhanced citation data
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get the column names from the citations table
        cursor.execute("PRAGMA table_info(citations)")
        columns = [column[1] for column in cursor.fetchall()]

        # Check if the enhanced columns exist, add them if not
        required_columns = [
            "context",
            "file_link",
            "volume",
            "reporter",
            "page",
            "court",
            "year",
        ]
        missing_columns = [col for col in required_columns if col not in columns]

        if missing_columns:
            logger.info(f"Adding missing columns to database: {missing_columns}")
            for column in missing_columns:
                try:
                    cursor.execute(f"ALTER TABLE citations ADD COLUMN {column} TEXT")
                    logger.info(f"Added column: {column}")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Could not add column {column}: {e}")

            conn.commit()

        conn.close()
    except Exception as e:
        logger.error(f"Error checking database schema: {e}")

    # Find all briefs
    briefs = find_briefs()
    logger.info(f"Found {len(briefs)} briefs to process")

    # Process each brief
    all_unverified_citations = []

    for brief in tqdm(briefs, desc="Processing briefs"):
        result = process_brief(brief)
        if result and "unverified_citations" in result:
            all_unverified_citations.extend(result["unverified_citations"])

    # Save all unverified citations
    save_unverified_citations(all_unverified_citations)

    logger.info(
        "Finished processing Washington briefs with enhanced citation validation"
    )
    logger.info(f"Total unverified citations: {len(all_unverified_citations)}")

    # Print a summary
    print("\nProcessing Summary:")
    print(f"Total briefs processed: {len(briefs)}")
    print(f"Total unverified citations: {len(all_unverified_citations)}")
    print(f"Results saved to: {RESULTS_DIR}")
    print(f"Unverified citations saved to: {CITATIONS_FILE}")
    print(f"File links saved to: {FILE_LINKS_DIR}")
    print("\nThe database has been updated with enhanced citation information:")
    print("  - Citation context (200 characters before and after each citation)")
    print("  - Links to source files")
    print("  - Detailed citation components (volume, reporter, page, court, year)")
    print(
        "\nYou can now use the enhanced citation validation features in the Vue.js interface."
    )

    # Suggest next steps
    print("\nNext steps:")
    print("1. Start the CaseStrainer application using start_casestrainer.bat")
    print("2. Navigate to the Enhanced Citation Validator in the Vue.js interface")
    print(
        "3. Test the enhanced citation validation with some of the extracted citations"
    )
    print("4. Check the citation context and file links for verified citations")
    logger.info(f"Results are saved in: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
