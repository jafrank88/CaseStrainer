"""
Add a sample citation to the citation database for testing.
"""

import os
import sqlite3
from citation_correction_engine import CitationCorrectionEngine


def add_sample_citation():
    """Add a sample citation to the database."""
    # Create an instance of the correction engine
    engine = CitationCorrectionEngine()

    try:
        # Connect to the database
        conn = sqlite3.connect(engine.db_path)
        cursor = conn.cursor()

        # Add a sample citation
        cursor.execute(
            """
        INSERT OR IGNORE INTO citations 
        (volume, reporter, page, case_name, court, year, normalized_citation, is_verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "123",
                "F.3d",
                "456",
                "Sample v. Test Case",
                "United States Court of Appeals for the Ninth Circuit",
                2023,
                "123 F.3d 456",
                1,
            ),
        )

        # Commit the changes
        conn.commit()
        print("Successfully added sample citation to the database.")

    except Exception as e:
        print(f"Error adding sample citation: {e}")
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("Adding sample citation to the database...")
    add_sample_citation()
    print("Done.")
