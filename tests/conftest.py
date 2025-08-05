"""
Shared fixtures for CaseStrainer tests
"""
import pytest
import os
import tempfile
from pathlib import Path


@pytest.fixture
def base_url():
    """Base URL for the application"""
    return "http://localhost:5000"


@pytest.fixture
def api_url():
    """API URL for the application"""
    return "http://localhost:5000/casestrainer/api"


@pytest.fixture
def health_url():
    """Health endpoint URL"""
    return "http://localhost:5000/casestrainer/api/health"


@pytest.fixture
def analyze_url():
    """Analyze endpoint URL"""
    return "http://localhost:5000/casestrainer/api/analyze"


@pytest.fixture
def test_text():
    """Sample test text with citations"""
    return """
    This is a test document with legal citations.
    
    Roe v. Wade, 410 U.S. 113 (1973).
    Brown v. Board of Education, 347 U.S. 483 (1954).
    
    The court held that the right to privacy is fundamental.
    """


@pytest.fixture
def temp_file():
    """Create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content with citations: Roe v. Wade, 410 U.S. 113 (1973).")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def test_data_dir():
    """Directory containing test data files"""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_pdf_path():
    """Path to a sample PDF file for testing"""
    # This would point to an actual test PDF file
    return Path(__file__).parent / "data" / "sample.pdf" 