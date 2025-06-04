"""
Initialize the citation database for the citation correction engine.
"""

import os
import sqlite3

# Database file path
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "citations.db")


def init_database():
    """Initialize the citation database with the required tables."""
    try:
        # Connect to the SQLite database (creates it if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the citations table
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            volume TEXT,
            reporter TEXT,
            page TEXT,
            case_name TEXT,
            court TEXT,
            year INTEGER,
            normalized_citation TEXT UNIQUE,
            is_verified BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        # Commit the table creation first
        conn.commit()

        # Check if the normalized_citation column exists, if not, add it
        cursor.execute("PRAGMA table_info(citations)")
        columns = [col[1] for col in cursor.fetchall()]

        if "normalized_citation" not in columns:
            cursor.execute(
                """
            ALTER TABLE citations
            ADD COLUMN normalized_citation TEXT UNIQUE
            """
            )

        # Create an index for faster lookups
        cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_normalized_citation 
        ON citations(normalized_citation)
        """
        )

        # Commit changes and close the connection
        conn.commit()
        print(f"Successfully initialized citation database at {db_path}")

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print("Initializing citation database...")
    init_database()
    print("Done.")
