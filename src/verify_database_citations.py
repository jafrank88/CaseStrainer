"""
Verify Citations from Unconfirmed Citations Database Tab

This script extracts citations from the Unconfirmed Citations Database tab
and verifies them using the multi-source verification tool.
"""

import json
import sqlite3


import random


from multi_source_verifier import MultiSourceVerifier
from src.config import DATABASE_FILE

# Constants
CONFIG_FILE = "config.json"
VERIFICATION_RESULTS_FILE = "database_verification_results.json"


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


def get_database_citations():
    """Get all citations from the Unconfirmed Citations Database tab."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if the unconfirmed_database_citations table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='unconfirmed_database_citations'"
    )
    if not cursor.fetchone():
        print("The unconfirmed_database_citations table does not exist. Creating it...")
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS unconfirmed_database_citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            citation_text TEXT NOT NULL,
            source TEXT,
            context TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            verification_status TEXT,
            verification_confidence REAL,
            verification_source TEXT,
            verification_tag TEXT
        )
        """
        )
        conn.commit()
        print(
            "Table created, but it's empty. Please add citations to the Unconfirmed Citations Database tab."
        )
        return []

    # Get all citations from the table
    cursor.execute("SELECT * FROM unconfirmed_database_citations")
    citations = [dict(row) for row in cursor.fetchall()]

    conn.close()

    print(
        f"Retrieved {len(citations)} citations from the Unconfirmed Citations Database tab"
    )
    return citations


def update_citation_verification(citation_id, verification_result):
    """Update the verification result for a citation in the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Add verification columns if they don't exist
    cursor.execute("PRAGMA table_info(unconfirmed_database_citations)")
    columns = [column[1] for column in cursor.fetchall()]

    if "verification_status" not in columns:
        cursor.execute(
            "ALTER TABLE unconfirmed_database_citations ADD COLUMN verification_status TEXT"
        )

    if "verification_confidence" not in columns:
        cursor.execute(
            "ALTER TABLE unconfirmed_database_citations ADD COLUMN verification_confidence REAL"
        )

    if "verification_source" not in columns:
        cursor.execute(
            "ALTER TABLE unconfirmed_database_citations ADD COLUMN verification_source TEXT"
        )

    if "verification_tag" not in columns:
        cursor.execute(
            "ALTER TABLE unconfirmed_database_citations ADD COLUMN verification_tag TEXT"
        )

    # Update the verification result
    found = verification_result.get("found", False)
    confidence = verification_result.get("confidence", 0.0)
    source = verification_result.get("source", "unknown")

    status = "VERIFIED" if found else "UNVERIFIED"

    # Add a special tag for citations verified by multi-source but not by CourtListener
    tag = None
    if found and source != "CourtListener" and source != "unknown":
        tag = "MULTI_SOURCE_ONLY"

    cursor.execute(
        "UPDATE unconfirmed_database_citations SET verification_status = ?, verification_confidence = ?, verification_source = ?, verification_tag = ? WHERE id = ?",
        (status, confidence, source, tag, citation_id),
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
    """Main function to verify citations from the Unconfirmed Citations Database tab."""
    print(
        "Starting verification of citations from the Unconfirmed Citations Database tab..."
    )

    # Load API keys
    api_keys = load_api_keys()
    print(f"Loaded API keys: {', '.join(api_keys.keys())}")

    # Create a MultiSourceVerifier
    verifier = MultiSourceVerifier(api_keys)

    # Get citations from the database
    citations = get_database_citations()

    if not citations:
        print("No citations found in the Unconfirmed Citations Database tab.")
        return

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

    # Analyze results
    verified_count = sum(
        1
        for r in verification_results
        if r.get("verification_result", {}).get("found", False)
    )
    multi_source_only = sum(
        1
        for r in verification_results
        if r.get("verification_result", {}).get("found", False)
        and r.get("verification_result", {}).get("source", "unknown") != "CourtListener"
        and r.get("verification_result", {}).get("source", "unknown") != "unknown"
    )

    print("\nVerification Summary:")
    print(f"Total citations: {len(citations)}")
    print(f"Verified citations: {verified_count} ({verified_count/len(citations):.2%})")
    print(f"Unverified citations: {len(citations) - verified_count}")
    print(
        f"Multi-source only verifications: {multi_source_only} ({multi_source_only/verified_count:.2%} of verified)"
        if verified_count > 0
        else "Multi-source only verifications: 0 (0.00%)"
    )

    print("\nCitation verification complete")
    print(f"Results saved to {VERIFICATION_RESULTS_FILE}")


if __name__ == "__main__":
    main()
