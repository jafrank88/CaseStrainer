"""
Populate Unconfirmed Citations Database Tab

This script extracts unverified citations from the main CaseStrainer database
and adds them to the Unconfirmed Citations Database tab for verification.
"""

import sqlite3
from src.config import DEFAULT_REQUEST_TIMEOUT, COURTLISTENER_TIMEOUT, CASEMINE_TIMEOUT, WEBSEARCH_TIMEOUT, SCRAPINGBEE_TIMEOUT

from datetime import datetime
import logging
from .config import get_database_path

DATABASE_FILE = get_database_path()

logger = logging.getLogger(__name__)


def setup_database_tables():
    """Set up the necessary database tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS unconfirmed_citations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        citation_text TEXT NOT NULL,
        brief_url TEXT,
        context TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verification_status TEXT,
        verification_confidence REAL,
        verification_source TEXT,
        verification_tag TEXT
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS unconfirmed_database_citations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        citation_text TEXT NOT NULL,
        source TEXT,
        context TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        verification_status TEXT,
        verification_confidence REAL,
        verification_source TEXT,
        verification_tag TEXT
    )
    """
    )

    conn.commit()
    conn.close()

    logger.info("Database tables set up successfully")


def get_unverified_citations():
    """Get all unverified citations from the main database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM unconfirmed_citations WHERE verification_status IS NULL OR verification_status = 'UNVERIFIED'"
    )
    citations = [dict(row) for row in cursor.fetchall()]

    conn.close()

    logger.info(f"Retrieved {len(citations)} unverified citations from the main database")
    return citations


def add_to_database_tab(citations):
    """Add unverified citations to the Unconfirmed Citations Database tab."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM unconfirmed_database_citations")

    count = 0
    for citation in citations:
        citation_text = citation["citation_text"]
        brief_url = citation.get("brief_url", "")
        context = citation.get("context", "")

        cursor.execute(
            "INSERT INTO unconfirmed_database_citations (citation_text, source, context, date_added) VALUES (?, ?, ?, ?)",
            (citation_text, brief_url, context, datetime.now()),
        )
        count += 1

    conn.commit()
    conn.close()

    logger.info(f"Added {count} citations to the Unconfirmed Citations Database tab")


def main():
    """Main function to populate the Unconfirmed Citations Database tab."""
    logger.info("Starting population of the Unconfirmed Citations Database tab...")

    setup_database_tables()

    citations = get_unverified_citations()

    if not citations:
        logger.info("No unverified citations found in the main database.")
        return

    add_to_database_tab(citations)

    logger.info("\nPopulation complete")
    logger.info("You can now run verify_database_citations.py to verify these citations using the multi-source tool")


if __name__ == "__main__":
    main()
