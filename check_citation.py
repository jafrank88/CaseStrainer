import sqlite3
import os


def check_citation(citation_text):
    """Check if a citation exists in the database and is verified."""
    db_path = os.path.join(os.path.dirname(__file__), "src", "citations.db")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if the citations table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='citations';
        """
        )
        if not cursor.fetchone():
            print("Error: 'citations' table does not exist in the database.")
            return False

        # Check if the citation exists and is verified
        cursor.execute(
            """
            SELECT citation_text, found 
            FROM citations 
            WHERE citation_text = ?;
        """,
            (citation_text,),
        )

        result = cursor.fetchone()

        if result:
            citation, found = result
            print(f"Citation found in database: {citation}")
            print(f"Verified (found=1): {bool(found)}")
            return bool(found)
        else:
            print(f"Citation '{citation_text}' not found in the database.")
            return False

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    citation = "534 F.3d 1290"
    print(f"Checking citation: {citation}")
    is_verified = check_citation(citation)
    print(f"Is verified: {is_verified}")
