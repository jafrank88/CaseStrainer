import os
import sqlite3
from pathlib import Path
from src.config import Config


def init_database():
    """Initialize the SQLite database with the required schema."""
    # Get the database path from config
    db_path = Config.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)

    # Create the database directory if it doesn't exist
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create citations table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                citation_text TEXT NOT NULL UNIQUE,
                found BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create an index on citation_text for faster lookups
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_citation_text ON citations (citation_text)
        """
        )

        # Create an index on found for faster filtering
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_citation_found ON citations (found)
        """
        )

        # Check if the database is empty
        cursor.execute("""SELECT COUNT(*) FROM citations""")
        count = cursor.fetchone()[0]

        # If database is empty, seed with some sample citations
        if count == 0:
            from src.citation_correction_engine import CitationCorrectionEngine

            engine = CitationCorrectionEngine()
            engine._init_database()

        conn.commit()
        print(f"Database initialized successfully at {db_path}")
        return True

    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    init_database()
