"""
Smoke test for CaseStrainer to verify basic functionality.
"""
import sys
import os
import unittest
from pathlib import Path

class TestSmoke(unittest.TestCase):
    """Basic smoke tests for CaseStrainer."""
    
    def test_imports(self):
        """Test that required modules can be imported."""
        try:
            # Try importing main application modules
            from src.citation_validator import CitationValidator
            from src.courtlistener_api import CourtListenerAPI
            from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier
            
            # If we get here, imports worked
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import required module: {e}")
    
    def test_environment(self):
        """Test that the environment is set up correctly."""
        # Check that we're running in the right directory
        self.assertTrue(Path("src").exists(), "src directory not found")
        self.assertTrue(Path("tests").exists(), "tests directory not found")
        
        # Check that required files exist
        required_files = [
            "requirements.txt",
            "README.md",
            "src/__init__.py",
        ]
        
        for file_path in required_files:
            self.assertTrue(
                Path(file_path).exists(),
                f"Required file not found: {file_path}"
            )

if __name__ == "__main__":
    unittest.main()
