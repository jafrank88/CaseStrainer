"""
Database Configuration Check Script

This script checks and verifies the database configuration for CaseStrainer.
It ensures the database file exists and is accessible, and provides detailed
information about the database configuration.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

# Import the config after adding to path
from src.config import DATABASE_FILE, BASE_DIR

def check_database_config():
    """Check and display database configuration details."""
    print("=== Database Configuration Check ===")
    print(f"Base directory: {BASE_DIR}")
    print(f"Database file path: {DATABASE_FILE}")
    
    # Check if database file exists
    db_exists = os.path.isfile(DATABASE_FILE)
    print(f"\nDatabase file exists: {'✅ Yes' if db_exists else '❌ No'}")
    
    if db_exists:
        # Get file info
        db_size = os.path.getsize(DATABASE_FILE) / (1024 * 1024)  # Size in MB
        print(f"Database size: {db_size:.2f} MB")
        
        # Try to connect to the database
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = cursor.fetchall()
            
            print(f"\nTables in database ({len(tables)}):")
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                print(f"  - {table[0]} ({len(columns)} columns)")
            
            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()
            print(f"\nDatabase integrity check: {integrity[0] if integrity else 'Failed'}")
            
            conn.close()
            print("\n✅ Database connection test successful")
            
        except sqlite3.Error as e:
            print(f"\n❌ Database connection error: {e}")
    else:
        print("\n⚠️  Database file does not exist. Creating an empty database...")
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
            
            # Create an empty database file
            with sqlite3.connect(DATABASE_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")  # Simple query to create the file
                conn.commit()
            
            print(f"✅ Created empty database at: {DATABASE_FILE}")
        except Exception as e:
            print(f"❌ Failed to create database: {e}")
            print("\nPlease check the following:")
            print(f"1. Directory permissions for: {os.path.dirname(DATABASE_FILE)}")
            print(f"2. Disk space on the drive containing: {os.path.splitdrive(DATABASE_FILE)[0]}")
            print(f"3. File system permissions for: {os.path.dirname(DATABASE_FILE)}")

if __name__ == "__main__":
    check_database_config()
