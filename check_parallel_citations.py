#!/usr/bin/env python3
"""
Script to check if parallel citations are being extracted and stored in the database.
"""

import sqlite3
import json
import os

def check_database():
    """Check the database for parallel citations."""
    db_path = "data/citations.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if parallel_citations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parallel_citations'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✓ parallel_citations table exists")
            
            # Check table schema
            cursor.execute("PRAGMA table_info(parallel_citations)")
            columns = cursor.fetchall()
            print(f"Table schema: {[col[1] for col in columns]}")
            
            # Count records
            cursor.execute("SELECT COUNT(*) FROM parallel_citations")
            count = cursor.fetchone()[0]
            print(f"Number of parallel citation records: {count}")
            
            # Show some examples
            if count > 0:
                cursor.execute("SELECT * FROM parallel_citations LIMIT 5")
                examples = cursor.fetchall()
                print("\nExample parallel citations:")
                for example in examples:
                    print(f"  {example}")
        else:
            print("✗ parallel_citations table does not exist")
        
        # Check main citations table for parallel_citations column
        cursor.execute("PRAGMA table_info(citations)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'parallel_citations' in column_names:
            print("✓ parallel_citations column exists in citations table")
            
            # Check for non-empty parallel citations
            cursor.execute("SELECT citation_text, parallel_citations FROM citations WHERE parallel_citations IS NOT NULL AND parallel_citations != '' LIMIT 5")
            examples = cursor.fetchall()
            
            if examples:
                print(f"Found {len(examples)} citations with parallel citations data:")
                for citation, parallel_data in examples:
                    try:
                        parsed = json.loads(parallel_data) if parallel_data else []
                        print(f"  {citation}: {parsed}")
                    except json.JSONDecodeError:
                        print(f"  {citation}: {parallel_data} (raw)")
            else:
                print("No citations found with parallel citations data")
        else:
            print("✗ parallel_citations column does not exist in citations table")
        
        # Check total citations
        cursor.execute("SELECT COUNT(*) FROM citations")
        total_citations = cursor.fetchone()[0]
        print(f"\nTotal citations in database: {total_citations}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database() 