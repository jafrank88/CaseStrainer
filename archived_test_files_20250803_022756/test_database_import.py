import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from database_manager import get_database_manager
    print("Successfully imported database_manager!")
    
    # Try to get the database manager instance
    db_manager = get_database_manager()
    print("Successfully got database manager instance!")
    
    # Try to access the DATABASE_FILE (should be set in config.py)
    from config import DATABASE_FILE
    print(f"DATABASE_FILE path: {DATABASE_FILE}")
    
    # Verify the database file exists
    if os.path.exists(DATABASE_FILE):
        print(f"Database file exists at: {DATABASE_FILE}")
    else:
        print(f"WARNING: Database file does not exist at: {DATABASE_FILE}")
        
except Exception as e:
    print(f"ERROR: {str(e)}", file=sys.stderr)
    raise
