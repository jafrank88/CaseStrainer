"""
Verify Unconfirmed Citations

This script checks all citations in the Unconfirmed Citations tab using
the enhanced citation verification tool with multiple sources.
"""

import os
import sys
import json
import sqlite3
import traceback
import time
import random
import requests
from datetime import datetime

# Import the multi-source verifier if available
try:
    from multi_source_verifier import MultiSourceVerifier

    print("Successfully imported MultiSourceVerifier")
except ImportError:
    print(
        "Error: Could not import MultiSourceVerifier. Make sure you're running this script from the CaseStrainer directory."
    )
    sys.exit(1)

# Constants
DATABASE_FILE = "citations.db"
CONFIG_FILE = "config.json"
VERIFICATION_RESULTS_FILE = "verification_results.json"


def load_api_keys():
    """Load API keys from config.json."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            return {
                "courtlistener": config.get("courtlistener_api_key"),
                "langsearch": config.get("langsearch_api_key"),
            }
    except Exception as e:
        print(f"Error loading API keys from config.json: {e}")
        return {}


def get_unconfirmed_citations():
    """Get all unconfirmed citations from the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM unconfirmed_citations")
    citations = [dict(row) for row in cursor.fetchall()]

    conn.close()

    print(f"Retrieved {len(citations)} unconfirmed citations from database")
    return citations


def update_citation_verification(citation_id, verification_result):
    """Update the verification result for a citation in the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Add verification_result column if it doesn't exist
    cursor.execute("PRAGMA table_info(unconfirmed_citations)")
    columns = [column[1] for column in cursor.fetchall()]

    if "verification_result" not in columns:
        cursor.execute(
            "ALTER TABLE unconfirmed_citations ADD COLUMN verification_result TEXT"
        )

    # Update the verification result
    cursor.execute(
        "UPDATE unconfirmed_citations SET verification_result = ? WHERE id = ?",
        (json.dumps(verification_result), citation_id),
    )

    conn.commit()
    conn.close()


def save_verification_results(results):
    """Save verification results to a JSON file."""
    try:
        with open(VERIFICATION_RESULTS_FILE, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Saved verification results to {VERIFICATION_RESULTS_FILE}")
    except Exception as e:
        print(f"Error saving verification results: {e}")


def main():
    """Main function to verify unconfirmed citations."""
    print("Starting verification of unconfirmed citations...")

    # Load API keys
    api_keys = load_api_keys()
    print(f"Loaded API keys: {', '.join(api_keys.keys())}")

    # Create a MultiSourceVerifier
    verifier = MultiSourceVerifier(api_keys)

    # Get unconfirmed citations
    citations = get_unconfirmed_citations()

    # Verify each citation
    verification_results = []

    for i, citation in enumerate(citations):
        citation_id = citation["id"]
        citation_text = citation["citation_text"]

        print(f"Verifying citation {i+1} of {len(citations)}: {citation_text}")

        try:
            # Verify the citation using multiple sources
            result = verifier.verify_citation(citation_text)

            # Add to results
            verification_results.append(
                {
                    "citation_id": citation_id,
                    "citation_text": citation_text,
                    "verification_result": result,
                }
            )

            # Update the database
            update_citation_verification(citation_id, result)

            # Add a delay to avoid overwhelming the APIs
            time.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"Error verifying citation: {e}")
            traceback.print_exc()

    # Save verification results
    save_verification_results(verification_results)

    print("Citation verification complete")
    print(f"Verified {len(verification_results)} citations")
    print(f"Results saved to {VERIFICATION_RESULTS_FILE}")


if __name__ == "__main__":
    main()
