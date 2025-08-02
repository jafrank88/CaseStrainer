"""
Import Unconfirmed Citations to CaseStrainer

This script imports the unconfirmed citations from the tab-delimited file
into CaseStrainer's database for display in the Unconfirmed Citations tab.
"""

import os
import sqlite3
import csv
import logging
from datetime import datetime
from .config import get_database_path

# Configure logging
logger = logging.getLogger(__name__)

# Constants
UNCONFIRMED_CITATIONS_FILE = "Unconfirmed_Citations_Tab.txt"
DATABASE_FILE = get_database_path()


def create_database_if_not_exists():
    """Create the citations database if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Create unconfirmed_citations table if it doesn't exist
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS unconfirmed_citations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        citation_text TEXT NOT NULL,
        brief_url TEXT,
        context TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    conn.commit()
    conn.close()

    logger.info(f"Database initialized: {DATABASE_FILE}")


def clear_existing_citations():
    """Clear existing unconfirmed citations from the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM unconfirmed_citations")

    conn.commit()
    conn.close()

    logger.info("Cleared existing unconfirmed citations from database")


def import_citations():
    """Import unconfirmed citations from the tab-delimited file."""
    if not os.path.exists(UNCONFIRMED_CITATIONS_FILE):
        logger.error(f"Error: {UNCONFIRMED_CITATIONS_FILE} not found")
        return

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Read the tab-delimited file
    with open(UNCONFIRMED_CITATIONS_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # Skip header row

        count = 0
        for row in reader:
            if len(row) >= 3:
                citation_text = row[0]
                brief_url = row[1]
                context = row[2]

                # Insert into database
                cursor.execute(
                    "INSERT INTO unconfirmed_citations (citation_text, brief_url, context, date_added) VALUES (?, ?, ?, ?)",
                    (citation_text, brief_url, context, datetime.now()),
                )
                count += 1

    conn.commit()
    conn.close()

    logger.info(f"Imported {count} unconfirmed citations to database")


def main():
    """Main function to import unconfirmed citations."""
    logger.info("Starting import of unconfirmed citations to CaseStrainer...")

    # Create database if it doesn't exist
    create_database_if_not_exists()

    # Clear existing citations
    clear_existing_citations()

    # Import citations
    import_citations()

    logger.info("Import complete. You can now view the unconfirmed citations in CaseStrainer's Unconfirmed Citations tab.")


if __name__ == "__main__":
    main()
