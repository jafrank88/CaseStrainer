"""
Smoke test for CaseStrainer to verify basic functionality.
"""
import sys
import os
import unittest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestSmoke(unittest.TestCase):
    """Basic smoke tests for CaseStrainer."""
    
    def test_imports(self):
        """Test that required modules can be imported."""
        try:
            # Try importing main application modules that actually exist
            from src.enhanced_unified_citation_processor import CitationValidator  # type: ignore
            from src.document_processing_unified import UnifiedDocumentProcessor  # type: ignore
            from src.redis_distributed_processor import RedisDistributedPDFSystem  # type: ignore
            
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
