#!/usr/bin/env python3
"""
Check the database schema to understand the column structure.
"""

import sqlite3
import os

def check_database_schema():
    """Check the database schema."""
    
    db_path = "data/citations.db"
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if citations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='citations'")
        if not cursor.fetchone():
            print("Citations table does not exist")
            return
        
        # Get table schema
        cursor.execute("PRAGMA table_info(citations)")
        columns = cursor.fetchall()
        
        print("Citations table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - {'PRIMARY KEY' if col[5] else ''}")
        
        # Check if parallel_citations table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parallel_citations'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(parallel_citations)")
            parallel_columns = cursor.fetchall()
            
            print("\nParallel_citations table columns:")
            for col in parallel_columns:
                print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - {'PRIMARY KEY' if col[5] else ''}")
        else:
            print("\nParallel_citations table does not exist")
        
        # Check sample data
        cursor.execute("SELECT * FROM citations LIMIT 3")
        sample_rows = cursor.fetchall()
        
        if sample_rows:
            print(f"\nSample data ({len(sample_rows)} rows):")
            for i, row in enumerate(sample_rows, 1):
                print(f"  Row {i}: {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking database schema: {e}")

if __name__ == "__main__":
    check_database_schema() 