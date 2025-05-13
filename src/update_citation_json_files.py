"""
Update Citation JSON Files

This script updates the JSON files with new citation data from the database
and clears the old ones to ensure the CaseStrainer application has the latest information.
"""

import os
import sys
import json
import logging
import sqlite3
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("citation_json_updater")

# Constants
USER_DOCS = os.path.join(os.path.expanduser('~'), 'Documents')
RESULTS_DIR = os.path.join(USER_DOCS, "WA_Briefs_Results")
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(REPO_DIR, "citations.db")

# JSON files to update
JSON_FILES = {
    "verified_citations.json": os.path.join(REPO_DIR, "verified_citations.json"),
    "unverified_citations.json": os.path.join(REPO_DIR, "unverified_citations.json"),
    "verification_results.json": os.path.join(REPO_DIR, "verification_results.json"),
    "truly_unverified_citations.json": os.path.join(REPO_DIR, "truly_unverified_citations.json")
}

# Backup directory
BACKUP_DIR = os.path.join(USER_DOCS, "CaseStrainer_Backups", datetime.now().strftime("%Y%m%d_%H%M%S"))

def backup_json_files():
    """Backup existing JSON files before updating them."""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logger.info(f"Created backup directory: {BACKUP_DIR}")
    
    for file_name, file_path in JSON_FILES.items():
        if os.path.exists(file_path):
            backup_path = os.path.join(BACKUP_DIR, file_name)
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backed up {file_name} to {backup_path}")

def clear_json_files():
    """Clear existing JSON files."""
    for file_name, file_path in JSON_FILES.items():
        if os.path.exists(file_path):
            # For verified_citations.json, create an empty structure
            if file_name == "verified_citations.json":
                with open(file_path, 'w') as f:
                    json.dump({"citations": []}, f)
            else:
                # For other files, create an empty array
                with open(file_path, 'w') as f:
                    json.dump([], f)
            
            logger.info(f"Cleared {file_name}")

def get_citations_from_database():
    """Get all citations from the database."""
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all citations
        cursor.execute("SELECT id, citation_text, case_name, confidence, found, explanation, source, source_document, url, context, date_added FROM citations")
        rows = cursor.fetchall()
        
        # Close the connection
        conn.close()
        
        # Convert to dictionaries
        citations = []
        for row in rows:
            citations.append({
                "id": row[0],
                "citation": row[1],  # citation_text
                "case_name": row[2],
                "confidence": row[3],
                "verified": bool(row[4]),  # found
                "explanation": row[5],
                "source": row[6],
                "source_document": row[7],
                "url": row[8],
                "context": row[9],
                "verification_date": row[10]  # date_added
            })
        
        return citations
    
    except Exception as e:
        logger.error(f"Error getting citations from database: {e}")
        return []

def update_verified_citations(citations):
    """Update the verified_citations.json file."""
    verified = {"citations": []}
    
    for citation in citations:
        if citation["verified"]:
            verified["citations"].append({
                "id": citation["id"],
                "citation": citation["citation"],
                "case_name": citation["case_name"],
                "confidence": citation["confidence"],
                "explanation": citation["explanation"],
                "source": citation["source"],
                "source_document": citation["source_document"],
                "url": citation["url"],
                "context": citation["context"],
                "verification_date": citation["verification_date"]
            })
    
    with open(JSON_FILES["verified_citations.json"], 'w') as f:
        json.dump(verified, f, indent=2)
    
    logger.info(f"Updated verified_citations.json with {len(verified['citations'])} citations")

def update_unverified_citations(citations):
    """Update the unverified_citations.json file."""
    unverified = []
    
    for citation in citations:
        if not citation["verified"]:
            unverified.append({
                "id": citation["id"],
                "citation": citation["citation"],
                "case_name": citation["case_name"],
                "confidence": citation["confidence"],
                "explanation": citation["explanation"],
                "source": citation["source"],
                "source_document": citation["source_document"],
                "context": citation["context"],
                "verification_date": citation["verification_date"]
            })
    
    with open(JSON_FILES["unverified_citations.json"], 'w') as f:
        json.dump(unverified, f, indent=2)
    
    logger.info(f"Updated unverified_citations.json with {len(unverified)} citations")

def update_verification_results(citations):
    """Update the verification_results.json file."""
    results = {
        "total": len(citations),
        "verified": len([c for c in citations if c["verified"]]),
        "unverified": len([c for c in citations if not c["verified"]]),
        "sources": {}
    }
    
    # Count citations by source
    for citation in citations:
        source = citation["source"]
        if source not in results["sources"]:
            results["sources"][source] = {
                "total": 0,
                "verified": 0,
                "unverified": 0
            }
        
        results["sources"][source]["total"] += 1
        if citation["verified"]:
            results["sources"][source]["verified"] += 1
        else:
            results["sources"][source]["unverified"] += 1
    
    with open(JSON_FILES["verification_results.json"], 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Updated verification_results.json with results for {len(citations)} citations")

def update_truly_unverified_citations(citations):
    """Update the truly_unverified_citations.json file."""
    truly_unverified = []
    
    for citation in citations:
        # Check if it's a Washington citation (either in source or citation text)
        is_wa_citation = ("WA" in citation["source"] if citation["source"] else False) or \
                        ("Wn." in citation["citation"] if citation["citation"] else False) or \
                        ("Wash." in citation["citation"] if citation["citation"] else False)
        
        if not citation["verified"] and is_wa_citation:
            truly_unverified.append({
                "id": citation["id"],
                "citation": citation["citation"],
                "case_name": citation["case_name"],
                "explanation": citation["explanation"],
                "source": citation["source"],
                "source_document": citation["source_document"],
                "context": citation["context"],
                "verification_date": citation["verification_date"]
            })
    
    with open(JSON_FILES["truly_unverified_citations.json"], 'w') as f:
        json.dump(truly_unverified, f, indent=2)
    
    logger.info(f"Updated truly_unverified_citations.json with {len(truly_unverified)} citations")

def copy_to_d_drive():
    """Copy the updated JSON files to the D: drive."""
    try:
        d_drive_dir = "D:\\CaseStrainer"
        
        if os.path.exists(d_drive_dir):
            for file_name, file_path in JSON_FILES.items():
                if os.path.exists(file_path):
                    d_drive_path = os.path.join(d_drive_dir, file_name)
                    shutil.copy2(file_path, d_drive_path)
                    logger.info(f"Copied {file_name} to {d_drive_path}")
        else:
            logger.warning(f"D: drive directory {d_drive_dir} does not exist. Files not copied.")
    
    except Exception as e:
        logger.error(f"Error copying files to D: drive: {e}")

def main():
    """Main function to update JSON files."""
    logger.info("Starting update of citation JSON files")
    
    # Backup existing JSON files
    backup_json_files()
    
    # Clear existing JSON files
    clear_json_files()
    
    # Get citations from the database
    citations = get_citations_from_database()
    logger.info(f"Retrieved {len(citations)} citations from the database")
    
    if citations:
        # Update JSON files
        update_verified_citations(citations)
        update_unverified_citations(citations)
        update_verification_results(citations)
        update_truly_unverified_citations(citations)
        
        # Copy to D: drive
        copy_to_d_drive()
    
    logger.info("Finished updating citation JSON files")

if __name__ == "__main__":
    main()
