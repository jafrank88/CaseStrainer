"""
Check Multitool Tab Functionality

This script checks if the multitool_confirmed_citations table exists and contains data,
and creates a simple API endpoint to test access to the data.
"""

import os
import sys
import json
import sqlite3
from flask import Flask, jsonify

# Constants
DATABASE_FILE = "citations.db"


def check_database():
    """Check if the multitool_confirmed_citations table exists and contains data."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Check if the table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='multitool_confirmed_citations'"
        )
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            print("Table 'multitool_confirmed_citations' does not exist")
            return False

        # Check if the table has data
        cursor.execute("SELECT COUNT(*) FROM multitool_confirmed_citations")
        count = cursor.fetchone()[0]

        print(f"Table 'multitool_confirmed_citations' contains {count} records")

        # Get a sample of the data
        cursor.execute("SELECT * FROM multitool_confirmed_citations LIMIT 1")
        sample = cursor.fetchone()

        if sample:
            columns = [description[0] for description in cursor.description]
            sample_dict = dict(zip(columns, sample))
            print("Sample data:")
            print(json.dumps(sample_dict, indent=2))

        conn.close()
        return count > 0
    except Exception as e:
        print(f"Error checking database: {e}")
        return False


def create_test_app():
    """Create a simple Flask app to test the API endpoint."""
    app = Flask(__name__)

    @app.route("/api/multitool_confirmed_citations")
    def get_multitool_confirmed_citations():
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM multitool_confirmed_citations")
            citations = [dict(row) for row in cursor.fetchall()]

            conn.close()

            return jsonify({"citations": citations})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


def main():
    """Main function to check the multitool tab functionality."""
    print("Checking multitool tab functionality...")

    # Check the database
    if not check_database():
        print(
            "Database check failed. Please ensure the multitool_confirmed_citations table exists and contains data."
        )
        return

    # Create and run a test app
    app = create_test_app()
    print("\nStarting test app on port 5050...")
    app.run(host="0.0.0.0", port=5050, debug=True)


if __name__ == "__main__":
    main()
