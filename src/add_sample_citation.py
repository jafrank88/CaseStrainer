"""
Add a sample citation to the citation database for testing.
"""

import sqlite3
from src.citation_correction_engine import CitationCorrectionEngine


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
        logger.info("Successfully added sample citation to the database.")

    except Exception as e:
        logger.error(f"Error adding sample citation: {e}")
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    logger.info("Adding sample citation to the database...")
    add_sample_citation()
    logger.info("Done.")
