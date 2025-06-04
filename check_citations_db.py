import sqlite3
import os


def check_database():
    db_path = os.path.join("src", "citations.db")

    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if citations table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='citations';"
        )
        if not cursor.fetchone():
            print("Citations table does not exist in the database.")
            return

        # Count total citations
        cursor.execute("SELECT COUNT(*) FROM citations;")
        total = cursor.fetchone()[0]
        print(f"Total citations in database: {total}")

        # Count verified citations
        cursor.execute("SELECT COUNT(*) FROM citations WHERE found = 1;")
        verified = cursor.fetchone()[0]
        print(f"Verified citations: {verified}")

        # Show some sample citations
        print("\nSample citations:")
        cursor.execute("SELECT * FROM citations LIMIT 5;")
        for row in cursor.fetchall():
            print(f"- {row[1]} (Found: {bool(row[4])})")

    except Exception as e:
        print(f"Error accessing database: {e}")
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    check_database()
