import sqlite3
import json

# Connect to the database
conn = sqlite3.connect("citations.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check if the multitool_confirmed_citations table exists
cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='multitool_confirmed_citations'"
)
table_exists = cursor.fetchone() is not None

print(f"Table exists: {table_exists}")

if table_exists:
    # Check the table structure
    cursor.execute("PRAGMA table_info(multitool_confirmed_citations)")
    columns = cursor.fetchall()
    print("\nTable structure:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

    # Count the records
    cursor.execute("SELECT COUNT(*) FROM multitool_confirmed_citations")
    count = cursor.fetchone()[0]
    print(f"\nTotal records: {count}")

    # Get a sample of records
    if count > 0:
        cursor.execute("SELECT * FROM multitool_confirmed_citations LIMIT 3")
        rows = cursor.fetchall()
        print("\nSample records:")
        for row in rows:
            row_dict = {key: row[key] for key in row.keys()}
            print(json.dumps(row_dict, indent=2))
    else:
        print("\nNo records found in the table.")
else:
    print("\nTable 'multitool_confirmed_citations' does not exist.")

    # List all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("\nAvailable tables:")
    for table in tables:
        print(f"  {table[0]}")

# Close the connection
conn.close()
