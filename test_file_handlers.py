#!/usr/bin/env python3
"""
Test script to verify file handlers can extract text properly
Tests PDF and text file extraction up to the point where we enqueue tasks
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pdf_handler():
    """Test PDF text extraction using the fast PDF handler"""
    logger.info("=== Testing PDF Handler ===")
    
    try:
        from src.pdf_handler import extract_text_from_pdf, PDF_HANDLER_AVAILABLE
        
        if not PDF_HANDLER_AVAILABLE:
            logger.error("PDF handler not available")
            return False
        
        # Test with a sample PDF file
        test_files = [
            "test_files/1029764.pdf",  # If this exists
            "1029764.pdf",  # Root directory
            "uploads/1029764.pdf"  # Uploads directory
        ]
        
        pdf_file = None
        for test_file in test_files:
            if os.path.exists(test_file):
                pdf_file = test_file
                break
        
        if not pdf_file:
            logger.warning("No test PDF file found, creating a simple test")
            # Create a simple test PDF if none exists
            try:
                from reportlab.pdfgen import canvas
                test_pdf_path = "test_simple.pdf"
                c = canvas.Canvas(test_pdf_path)
                c.drawString(100, 750, "Test PDF content for citation extraction")
                c.drawString(100, 700, "This is a test document with sample text")
                c.drawString(100, 650, "Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)")
                c.save()
                pdf_file = test_pdf_path
                logger.info(f"Created test PDF: {pdf_file}")
            except ImportError:
                logger.error("reportlab not available, cannot create test PDF")
                return False
        
        logger.info(f"Testing PDF extraction with: {pdf_file}")
        
        # Test with timeout
        start_time = time.time()
        try:
            extracted_text = extract_text_from_pdf(pdf_file, timeout=25)
            extraction_time = time.time() - start_time
            
            logger.info(f"PDF extraction completed in {extraction_time:.2f} seconds")
            logger.info(f"Extracted text length: {len(extracted_text)}")
            logger.info(f"First 200 characters: {extracted_text[:200]}")
            
            if extracted_text and extracted_text.strip():
                logger.info("✓ PDF extraction successful")
                return True
            else:
                logger.error("✗ PDF extraction returned empty text")
                return False
                
        except Exception as e:
            logger.error(f"✗ PDF extraction failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"✗ PDF handler test failed: {e}")
        return False

def test_document_processing_unified():
    """Test text file extraction using document_processing_unified"""
    logger.info("=== Testing Document Processing Unified ===")
    
    try:
        from src.document_processing_unified import extract_text_from_file
        
        # Test with a sample text file
        test_files = [
            "test_files/test.txt",
            "test.txt",
            "uploads/test.txt"
        ]
        
        text_file = None
        for test_file in test_files:
            if os.path.exists(test_file):
                text_file = test_file
                break
        
        if not text_file:
            logger.info("Creating test text file")
            test_content = """
            Test document content for citation extraction.
            
            This is a sample legal document with citations:
            Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022)
            Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011)
            Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)
            
            This should be extracted properly by the document processor.
            """
            
            test_txt_path = "test_simple.txt"
            with open(test_txt_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            text_file = test_txt_path
            logger.info(f"Created test text file: {text_file}")
        
        logger.info(f"Testing text extraction with: {text_file}")
        
        start_time = time.time()
        try:
            extracted_text = extract_text_from_file(text_file)
            extraction_time = time.time() - start_time
            
            logger.info(f"Text extraction completed in {extraction_time:.2f} seconds")
            logger.info(f"Extracted text length: {len(extracted_text)}")
            logger.info(f"First 200 characters: {extracted_text[:200]}")
            
            if extracted_text and extracted_text.strip():
                logger.info("✓ Text extraction successful")
                return True
            else:
                logger.error("✗ Text extraction returned empty text")
                return False
                
        except Exception as e:
            logger.error(f"✗ Text extraction failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Document processing unified test failed: {e}")
        return False

def test_file_upload_simulation():
    """Simulate the file upload process from the API endpoint"""
    logger.info("=== Testing File Upload Simulation ===")
    
    try:
        # Simulate the file upload process
        file_ext = '.pdf'
        filename = 'test_simulation.pdf'
        
        # Check if we have a test PDF
        test_pdf = None
        for test_file in ["test_simple.pdf", "1029764.pdf", "test_files/1029764.pdf"]:
            if os.path.exists(test_file):
                test_pdf = test_file
                break
        
        if not test_pdf:
            logger.warning("No test PDF available for simulation")
            return False
        
        logger.info(f"Simulating file upload with: {test_pdf}")
        
        # Simulate the extraction process from vue_api_endpoints.py
        try:
            from src.pdf_handler import extract_text_from_pdf, PDF_HANDLER_AVAILABLE
            
            if file_ext.lower() == '.pdf' and PDF_HANDLER_AVAILABLE:
                logger.info(f"Using fast PDF handler for: {filename}")
                extracted_text = extract_text_from_pdf(test_pdf, timeout=25)
            else:
                logger.info("Using document_processing_unified fallback")
                from src.document_processing_unified import extract_text_from_file
                extracted_text = extract_text_from_file(test_pdf)
            
            logger.info(f"Simulation extraction completed. Length: {len(extracted_text)}")
            
            if not extracted_text or not extracted_text.strip():
                logger.error("✗ Simulation: Extracted text is empty")
                return False
            
            # Simulate creating the task data structure
            task_data = {
                'text': extracted_text,
                'filename': filename,
                'file_ext': file_ext,
                'source_type': 'file'
            }
            
            logger.info(f"✓ Simulation: Task data created successfully")
            logger.info(f"Task data keys: {list(task_data.keys())}")
            logger.info(f"Text length in task: {len(task_data['text'])}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Simulation failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"✗ File upload simulation failed: {e}")
        return False

def cleanup_test_files():
    """Clean up test files created during testing"""
    logger.info("=== Cleaning up test files ===")
    
    test_files = ["test_simple.pdf", "test_simple.txt"]
    for test_file in test_files:
        if os.path.exists(test_file):
            try:
                os.remove(test_file)
                logger.info(f"Cleaned up: {test_file}")
            except Exception as e:
                logger.warning(f"Could not clean up {test_file}: {e}")

def main():
    """Run all file handler tests"""
    logger.info("Starting file handler tests...")
    
    results = []
    
    # Test PDF handler
    results.append(("PDF Handler", test_pdf_handler()))
    
    # Test document processing unified
    results.append(("Document Processing Unified", test_document_processing_unified()))
    
    # Test file upload simulation
    results.append(("File Upload Simulation", test_file_upload_simulation()))
    
    # Clean up
    cleanup_test_files()
    
    # Summary
    logger.info("\n=== Test Results Summary ===")
    all_passed = True
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All tests passed! File handlers are working correctly.")
    else:
        logger.error("\n❌ Some tests failed. Check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 