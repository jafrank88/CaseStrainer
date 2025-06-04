import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "src", "citations.db")

try:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get table information
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in the database:")
    for table in tables:
        print(f"- {table[0]}")

        # Get column information for each table
        cursor.execute(f"PRAGMA table_info({table[0]});")
        columns = cursor.fetchall()
        print(f"  Columns: {', '.join([col[1] for col in columns])}")

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]};")
        count = cursor.fetchone()[0]
        print(f"  Rows: {count}")

        # Show first few rows if table is not empty
        if count > 0:
            cursor.execute(f"SELECT * FROM {table[0]} LIMIT 3;")
            rows = cursor.fetchall()
            print("  Sample rows:")
            for row in rows:
                print(f"  - {row}")

    # Close the connection
    conn.close()

except Exception as e:
    print(f"Error checking database: {e}")
