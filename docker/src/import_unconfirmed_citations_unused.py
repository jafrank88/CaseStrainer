"""
Import Unconfirmed Citations to CaseStrainer

This script imports the unconfirmed citations from the tab-delimited file
into CaseStrainer's database for display in the Unconfirmed Citations tab.
"""

import os
import sys
import json
import sqlite3
import csv
from datetime import datetime

# Constants
UNCONFIRMED_CITATIONS_FILE = "Unconfirmed_Citations_Tab.txt"
DATABASE_FILE = "citations.db"


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

    print(f"Database initialized: {DATABASE_FILE}")


def clear_existing_citations():
    """Clear existing unconfirmed citations from the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM unconfirmed_citations")

    conn.commit()
    conn.close()

    print("Cleared existing unconfirmed citations from database")


def import_citations():
    """Import unconfirmed citations from the tab-delimited file."""
    if not os.path.exists(UNCONFIRMED_CITATIONS_FILE):
        print(f"Error: {UNCONFIRMED_CITATIONS_FILE} not found")
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

    print(f"Imported {count} unconfirmed citations to database")


def main():
    """Main function to import unconfirmed citations."""
    print("Starting import of unconfirmed citations to CaseStrainer...")

    # Create database if it doesn't exist
    create_database_if_not_exists()

    # Clear existing citations
    clear_existing_citations()

    # Import citations
    import_citations()

    print(
        "Import complete. You can now view the unconfirmed citations in CaseStrainer's Unconfirmed Citations tab."
    )


if __name__ == "__main__":
    main()
