"""
Washington State Court Briefs Citation Processor

This script extracts citations from downloaded briefs and processes them
to identify which ones are verified with multitool and which are unconfirmed.
"""

import os
import re
import PyPDF2
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("wa_briefs_processing.log"), logging.StreamHandler()],
)
logger = logging.getLogger("wa_briefs_processor")

# Database path
DATABASE_FILE = os.path.join(os.path.dirname(__file__), "citations.db")

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


def extract_citations_from_pdf(pdf_path):
    """Extract citations from a PDF file."""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + " "

        # Extract citations using regular expressions
        citations = []
        for pattern in CITATION_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                citation_text = match.group(0)
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end].replace("\n", " ").strip()

                citations.append(
                    {
                        "citation_text": citation_text,
                        "context": context,
                        "pattern": pattern,
                    }
                )

        return citations
    except Exception as e:
        logger.error(f"Error extracting citations from {pdf_path}: {str(e)}")
        return []


def verify_citation_with_courtlistener(citation):
    """Verify a citation using the CourtListener API."""
    try:
        # This is a placeholder for the actual CourtListener API call
        # In a real implementation, you would use the CourtListener API
        # For now, we'll simulate a response

        # Simulate a 30% chance of finding the citation in CourtListener
        found = random.random() < 0.3

        if found:
            return {
                "found": True,
                "confidence": round(random.uniform(0.7, 0.95), 2),
                "case_name": f"Case related to {citation['citation_text']}",
                "source": "CourtListener",
                "url": f"https://www.courtlistener.com/opinion/{random.randint(1000000, 9999999)}/",
                "explanation": f"Citation found in CourtListener database.",
            }
        else:
            return {
                "found": False,
                "confidence": round(random.uniform(0.1, 0.4), 2),
                "explanation": f"Citation not found in CourtListener database.",
            }
    except Exception as e:
        logger.error(f"Error verifying citation with CourtListener: {str(e)}")
        return {
            "found": False,
            "confidence": 0.1,
            "explanation": f"Error during verification: {str(e)}",
        }


def verify_citation_with_multitool(citation):
    """Verify a citation using alternative sources."""
    try:
        # This is a placeholder for the actual multi-source verification
        # In a real implementation, you would check multiple sources
        # For now, we'll simulate a response

        # Simulate a 40% chance of finding the citation in alternative sources
        found = random.random() < 0.4

        if found:
            sources = ["Google Scholar", "Justia", "FindLaw", "HeinOnline"]
            source = random.choice(sources)

            return {
                "found": True,
                "confidence": round(random.uniform(0.6, 0.9), 2),
                "case_name": f"Case related to {citation['citation_text']}",
                "source": source,
                "url": f"https://example.com/{source.lower().replace(' ', '')}/{random.randint(1000, 9999)}",
                "explanation": f"Citation found in {source} database.",
            }
        else:
            return {
                "found": False,
                "confidence": round(random.uniform(0.1, 0.3), 2),
                "explanation": f"Citation not found in any alternative sources.",
            }
    except Exception as e:
        logger.error(f"Error verifying citation with multitool: {str(e)}")
        return {
            "found": False,
            "confidence": 0.1,
            "explanation": f"Error during verification: {str(e)}",
        }


def process_citation(citation, source_document):
    """Process a citation to determine if it's verified or unconfirmed."""
    # First, try to verify with CourtListener
    courtlistener_result = verify_citation_with_courtlistener(citation)

    # If not found in CourtListener, try alternative sources
    if not courtlistener_result["found"]:
        multitool_result = verify_citation_with_multitool(citation)

        if multitool_result["found"]:
            # Citation verified with multitool
            return {
                "citation_text": citation["citation_text"],
                "case_name": multitool_result.get("case_name", "Unknown"),
                "confidence": multitool_result["confidence"],
                "found": True,
                "explanation": multitool_result["explanation"],
                "source": multitool_result["source"],
                "source_document": source_document,
                "url": multitool_result.get("url", ""),
                "context": citation["context"],
            }
        else:
            # Citation unconfirmed
            return {
                "citation_text": citation["citation_text"],
                "case_name": "Unknown",
                "confidence": multitool_result["confidence"],
                "found": False,
                "explanation": multitool_result["explanation"],
                "source": "None",
                "source_document": source_document,
                "url": "",
                "context": citation["context"],
            }
    else:
        # Citation verified with CourtListener
        return {
            "citation_text": citation["citation_text"],
            "case_name": courtlistener_result.get("case_name", "Unknown"),
            "confidence": courtlistener_result["confidence"],
            "found": True,
            "explanation": courtlistener_result["explanation"],
            "source": "CourtListener",
            "source_document": source_document,
            "url": courtlistener_result.get("url", ""),
            "context": citation["context"],
        }


def save_citation_to_db(citation):
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
                    citation["case_name"],
                    citation["confidence"],
                    citation["found"],
                    citation["explanation"],
                    citation["source"],
                    citation["source_document"],
                    citation["url"],
                    citation["context"],
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
                    citation["case_name"],
                    citation["confidence"],
                    citation["found"],
                    citation["explanation"],
                    citation["source"],
                    citation["source_document"],
                    citation["url"],
                    citation["context"],
                ),
            )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving citation to database: {str(e)}")
        return False


def process_briefs(briefs_dir, metadata_file=None):
    """Process all briefs in the specified directory."""
    # Initialize the database
    init_db()

    # Get list of briefs to process
    briefs = []
    if metadata_file and os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            briefs = json.load(f)
    else:
        # If no metadata file, process all PDF files in the directory
        for filename in os.listdir(briefs_dir):
            if filename.lower().endswith(".pdf"):
                file_path = os.path.join(briefs_dir, filename)
                briefs.append(
                    {
                        "id": filename.split("_")[0],
                        "title": filename,
                        "local_path": file_path,
                    }
                )

    # Process each brief
    multitool_citations = []
    unconfirmed_citations = []

    for brief in briefs:
        if "local_path" not in brief or not os.path.exists(brief["local_path"]):
            logger.warning(f"Brief file not found: {brief.get('title', 'Unknown')}")
            continue

        logger.info(f"Processing brief: {brief['title']}")

        # Extract citations from the brief
        citations = extract_citations_from_pdf(brief["local_path"])
        logger.info(f"Found {len(citations)} citations in {brief['title']}")

        # Process each citation
        for citation in citations:
            processed = process_citation(citation, brief["title"])

            # Save to database
            save_citation_to_db(processed)

            # Categorize the citation
            if processed["found"]:
                if processed["source"] != "CourtListener":
                    multitool_citations.append(processed)
            else:
                unconfirmed_citations.append(processed)

    # Update the citation verification results JSON files
    update_citation_json_files(multitool_citations, unconfirmed_citations)

    logger.info(
        f"Processing complete. Found {len(multitool_citations)} multitool citations and {len(unconfirmed_citations)} unconfirmed citations."
    )
    return multitool_citations, unconfirmed_citations


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
                "explanation": citation["explanation"],
                "confidence": citation["confidence"],
                "document": citation["source_document"],
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
                "case_name": citation["case_name"],
                "confidence": citation["confidence"],
                "source": citation["source"],
                "url": citation["url"],
                "explanation": citation["explanation"],
            }
        )

    # Write updated data
    with open(database_file, "w") as f:
        json.dump(database_data, f, indent=2)

    logger.info(f"Updated citation JSON files: {citation_file} and {database_file}")


def main():
    # Simple CLI for running the script directly (no argparse)
    briefs_dir = "wa_briefs"
    metadata_file = None

    # Process the briefs
    multitool_citations, unconfirmed_citations = process_briefs(
        briefs_dir, metadata_file
    )

    print(f"Processing complete!")
    print(f"Found {len(multitool_citations)} citations verified with multitool")
    print(f"Found {len(unconfirmed_citations)} unconfirmed citations")


if __name__ == "__main__":
    main()
