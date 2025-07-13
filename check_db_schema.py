#!/usr/bin/env python3
"""
Check the database schema to see what columns are available.
"""

import sqlite3
import os

def check_database_schema():
    """Check the database schema."""
    db_path = os.path.join('data', 'citations.db')
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("DATABASE TABLES:")
        for table in tables:
            print(f"  - {table[0]}")
        
        print("\nTABLE SCHEMAS:")
        for table in tables:
            table_name = table[0]
            print(f"\n{table_name}:")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        
        # Show some sample data
        print("\nSAMPLE DATA:")
        for table in tables:
            table_name = table[0]
            print(f"\n{table_name} (first 3 rows):")
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {row}")
        
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database_schema() 