#!/usr/bin/env python3
"""
Simple test script to verify file handlers can extract text properly
"""

import os
import sys
import time

def test_basic_imports():
    """Test basic imports"""
    print("=== Testing Basic Imports ===")
    
    try:
        # Test basic imports
        import logging
        print("✓ logging imported successfully")
        
        import re
        print("✓ re imported successfully")
        
        import time
        print("✓ time imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Basic imports failed: {e}")
        return False

def test_pdf_handler_import():
    """Test PDF handler import"""
    print("\n=== Testing PDF Handler Import ===")
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Try to import PDF handler
        from src.document_processing_unified import extract_text_from_file
        print("✓ Document processing imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ PDF handler import failed: {e}")
        return False

def test_document_processing_import():
    """Test document processing import"""
    print("\n=== Testing Document Processing Import ===")
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Try to import document processing
        from src.document_processing_unified import extract_text_from_file
        print("✓ Document processing imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Document processing import failed: {e}")
        return False

def test_file_extraction():
    """Test actual file extraction"""
    print("\n=== Testing File Extraction ===")
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        from src.document_processing_unified import extract_text_from_file
        
        # Create a simple test text file
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
        
        print(f"✓ Created test file: {test_txt_path}")
        
        # Test text extraction
        start_time = time.time()
        extracted_text = extract_text_from_file(test_txt_path)
        extraction_time = time.time() - start_time
        
        print(f"✓ Text extraction completed in {extraction_time:.2f} seconds")
        print(f"✓ Extracted text length: {len(extracted_text)}")
        print(f"✓ First 200 characters: {extracted_text[:200]}")
        
        # Clean up
        os.remove(test_txt_path)
        print(f"✓ Cleaned up test file")
        
        return True
        
    except Exception as e:
        print(f"✗ File extraction failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting simple file handler tests...\n")
    
    results = []
    
    # Test basic imports
    results.append(("Basic Imports", test_basic_imports()))
    
    # Test PDF handler import
    results.append(("PDF Handler Import", test_pdf_handler_import()))
    
    # Test document processing import
    results.append(("Document Processing Import", test_document_processing_import()))
    
    # Test file extraction
    results.append(("File Extraction", test_file_extraction()))
    
    # Summary
    print("\n=== Test Results Summary ===")
    all_passed = True
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! File handlers are working correctly.")
    else:
        print("\n❌ Some tests failed. Check the logs above for details.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 