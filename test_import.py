import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

try:
    from src.api.services.citation_service import CitationService
    print("Successfully imported CitationService")
except ImportError as e:
    print(f"Error importing CitationService: {e}")
    print(f"Python path: {sys.path}")
    print(f"Current working directory: {os.getcwd()}")
