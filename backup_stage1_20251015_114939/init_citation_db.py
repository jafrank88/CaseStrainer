import os
import sqlite3
from src.config import DATABASE_FILE


def init_database():
    """Initialize the SQLite database with the required schema."""
    # Get the database path from config
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), DATABASE_FILE
    )
    db_dir = os.path.dirname(db_path)

    # Create the database directory if it doesn't exist
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    print(f"Initializing database at: {db_path}")

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
            print("Seeding database with sample citations...")
            sample_citations = [
                # US Supreme Court cases
                "410 U.S. 113",  # Roe v. Wade
                "347 U.S. 483",  # Brown v. Board of Education
                "384 U.S. 436",  # Miranda v. Arizona
                "163 U.S. 537",  # Plessy v. Ferguson
                "5 U.S. 137",  # Marbury v. Madison
                # Federal Reporter cases
                "347 F.3d 123",
                "456 F.2d 789",
                "789 F.3d 456",
                "123 F.Supp.2d 456",
                "456 F.Supp.2d 789",
                # Washington State cases
                "123 Wn.2d 456",
                "456 Wn. App. 789",
                "789 Wn.2d 123",
                "123 Wn. App. 456",
                "456 Wn. 789",
            ]

            # Insert sample citations
            for citation in sample_citations:
                try:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO citations (citation_text, found)
                        VALUES (?, 1)
                    """,
                        (citation,),
                    )
                    print(f"Added citation: {citation}")
                except Exception as e:
                    print(f"Could not insert citation {citation}: {e}")

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
