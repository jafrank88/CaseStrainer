import os
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from src.pdf_handler import (
    PDFHandler,
    PDFExtractionConfig,
    PDFExtractionMethod,
    clean_extracted_text
)

# Test data
SAMPLE_PDF_CONTENT = b'%PDF-1.7\n%Test PDF content'
SAMPLE_TEXT = "This is a test PDF with some citations like 123 U.S. 456 and 789 F.2d 101"
SAMPLE_CLEANED_TEXT = "This is a test PDF with some citations like 123 U.S. 456 and 789 F. 101"

@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(SAMPLE_PDF_CONTENT)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def pdf_handler():
    """Create a PDFHandler instance with test configuration."""
    config = PDFExtractionConfig(
        timeout=5,
        max_text_length=100,
        preferred_method=PDFExtractionMethod.PYPDF2,
        use_fallback=True,
        clean_text=True,
        debug=True
    )
    return PDFHandler(config)

@pytest.fixture
def mock_pypdf2():
    """Mock PyPDF2 for testing."""
    with patch('src.pdf_handler.PyPDF2') as mock:
        # Create mock PDF reader
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [
            MagicMock(extract_text=lambda: SAMPLE_TEXT),
            MagicMock(extract_text=lambda: "Page 2")
        ]
        mock.PdfReader.return_value = mock_reader
        yield mock

@pytest.fixture
def mock_pdfminer():
    """Mock pdfminer for testing."""
    with patch('src.pdf_handler.pdfminer_extract_text') as mock:
        mock.return_value = SAMPLE_TEXT
        yield mock

@pytest.fixture
def mock_pdftotext():
    """Mock pdftotext command for testing."""
    with patch('subprocess.run') as mock:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""
        mock.return_value = mock_process
        yield mock

class TestPDFHandler:
    """Test suite for PDFHandler class."""
    
    def test_init_default_config(self):
        """Test initialization with default configuration."""
        handler = PDFHandler()
        assert handler.config.timeout == 25
        assert handler.config.preferred_method == PDFExtractionMethod.PYPDF2
        assert handler.config.use_fallback is True
        
    def test_init_custom_config(self):
        """Test initialization with custom configuration."""
        config = PDFExtractionConfig(
            timeout=10,
            preferred_method=PDFExtractionMethod.PDFMINER,
            use_fallback=False
        )
        handler = PDFHandler(config)
        assert handler.config.timeout == 10
        assert handler.config.preferred_method == PDFExtractionMethod.PDFMINER
        assert handler.config.use_fallback is False
        
    def test_validate_pdf_header_valid(self, temp_pdf_file):
        """Test PDF header validation with valid PDF."""
        handler = PDFHandler()
        is_valid, msg, metadata = handler._validate_pdf_header(temp_pdf_file)
        assert is_valid is True
        assert "Valid PDF header" in msg
        assert metadata['header_valid'] is True
        
    def test_validate_pdf_header_invalid(self, tmp_path):
        """Test PDF header validation with invalid PDF."""
        invalid_pdf = tmp_path / "invalid.pdf"
        invalid_pdf.write_bytes(b'Not a PDF file')
        handler = PDFHandler()
        is_valid, msg, metadata = handler._validate_pdf_header(str(invalid_pdf))
        assert is_valid is False
        assert "Invalid PDF file" in msg
        
    def test_extract_with_pypdf2_success(self, temp_pdf_file, mock_pypdf2):
        """Test successful text extraction with PyPDF2."""
        handler = PDFHandler()
        text, error = handler._extract_with_pypdf2(temp_pdf_file, 0)
        assert text == SAMPLE_TEXT + "\nPage 2\n"
        assert error is None
        
    def test_extract_with_pypdf2_encrypted(self, temp_pdf_file, mock_pypdf2):
        """Test PyPDF2 extraction with encrypted PDF."""
        mock_pypdf2.PdfReader.return_value.is_encrypted = True
        handler = PDFHandler()
        text, error = handler._extract_with_pypdf2(temp_pdf_file, 0)
        assert text is None
        assert "encrypted" in error.lower()
        
    def test_extract_with_pdfminer_success(self, temp_pdf_file, mock_pdfminer):
        """Test successful text extraction with pdfminer."""
        handler = PDFHandler()
        text, error = handler._extract_with_pdfminer(temp_pdf_file, 0)
        assert text == SAMPLE_TEXT
        assert error is None
        
    def test_extract_with_pdftotext_success(self, temp_pdf_file, mock_pdftotext):
        """Test successful text extraction with pdftotext."""
        with patch('builtins.open', mock_open(read_data=SAMPLE_TEXT)):
            handler = PDFHandler()
            text, error = handler._extract_with_pdftotext(temp_pdf_file, 0)
            assert text == SAMPLE_TEXT
            assert error is None
            
    def test_extract_text_preferred_method(self, temp_pdf_file, mock_pypdf2):
        """Test text extraction using preferred method."""
        handler = PDFHandler(PDFExtractionConfig(
            preferred_method=PDFExtractionMethod.PYPDF2
        ))
        text = handler.extract_text(temp_pdf_file)
        assert SAMPLE_TEXT in text
        
    def test_extract_text_fallback(self, temp_pdf_file, mock_pypdf2, mock_pdfminer):
        """Test text extraction with fallback to alternative method."""
        # Make PyPDF2 fail
        mock_pypdf2.PdfReader.side_effect = Exception("PyPDF2 failed")
        handler = PDFHandler(PDFExtractionConfig(
            preferred_method=PDFExtractionMethod.PYPDF2,
            use_fallback=True
        ))
        text = handler.extract_text(temp_pdf_file)
        assert SAMPLE_TEXT in text
        
    def test_extract_text_timeout(self, temp_pdf_file, mock_pypdf2):
        """Test text extraction timeout handling."""
        def slow_extract():
            import time
            time.sleep(1)
            return SAMPLE_TEXT
            
        mock_pypdf2.PdfReader.return_value.pages[0].extract_text = slow_extract
        handler = PDFHandler(PDFExtractionConfig(timeout=0.1))
        text = handler.extract_text(temp_pdf_file)
        assert "timed out" in text.lower()
        
    def test_handle_problematic_pdf(self, temp_pdf_file, mock_pypdf2, mock_pdfminer, mock_pdftotext):
        """Test handling of problematic PDFs."""
        handler = PDFHandler()
        # Make PyPDF2 fail
        mock_pypdf2.PdfReader.side_effect = Exception("PyPDF2 failed")
        # Make pdfminer succeed
        mock_pdfminer.return_value = SAMPLE_TEXT
        
        text, error = handler._handle_problematic_pdf(temp_pdf_file)
        assert text == SAMPLE_TEXT
        assert error is None
        
    def test_sanitize_text_for_logging(self):
        """Test text sanitization for logging."""
        handler = PDFHandler()
        # Test with normal text
        text = "Normal text"
        assert handler._sanitize_text_for_logging(text) == text
        
        # Test with long text
        long_text = "x" * 300
        sanitized = handler._sanitize_text_for_logging(long_text)
        assert len(sanitized) == handler.config.max_text_length + 3  # +3 for "..."
        
        # Test with binary data
        binary = b'\x00\x01\x02'
        assert handler._sanitize_text_for_logging(binary) == "[Binary data]"
        
    def test_sanitize_bytes_for_logging(self):
        """Test bytes sanitization for logging."""
        handler = PDFHandler()
        # Test with normal bytes
        bytes_data = b'Test'
        assert handler._sanitize_bytes_for_logging(bytes_data) == "54 65 73 74"
        
        # Test with long bytes
        long_bytes = b'x' * 300
        sanitized = handler._sanitize_bytes_for_logging(long_bytes)
        assert len(sanitized) <= handler.config.max_text_length + 3  # +3 for "..."
        
        # Test with empty bytes
        assert handler._sanitize_bytes_for_logging(b'') == ""


class TestCleanExtractedText:
    """Test suite for clean_extracted_text function."""
    
    def test_clean_normal_text(self):
        """Test cleaning of normal text."""
        text = "Normal text with no citations"
        assert clean_extracted_text(text) == text
        
    def test_clean_citations(self):
        """Test cleaning of text with citations."""
        text = "123 U.S. 456 and 789 F.2d 101"
        cleaned = clean_extracted_text(text)
        assert "123 U.S. 456" in cleaned
        assert "789 F. 101" in cleaned
        
    def test_clean_ocr_errors(self):
        """Test cleaning of OCR errors."""
        text = "123 O.S. 456 and 789 l.Ed. 101"
        cleaned = clean_extracted_text(text)
        assert "123 0.S. 456" in cleaned
        assert "789 1.Ed. 101" in cleaned
        
    def test_clean_empty_text(self):
        """Test cleaning of empty text."""
        assert clean_extracted_text("") == ""
        assert clean_extracted_text(None) == ""
        
    def test_clean_preserves_citation_patterns(self):
        """Test that citation patterns are preserved."""
        text = "123 U.S. 456\n789 F.2d 101"
        cleaned = clean_extracted_text(text)
        assert "123 U.S. 456" in cleaned
        assert "789 F. 101" in cleaned
        assert "\n" not in cleaned  # Line breaks should be removed


if __name__ == '__main__':
    pytest.main([__file__]) 