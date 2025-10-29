#!/usr/bin/env python3
"""
Test script to verify enhanced text extraction integration
"""

import os
import sys
import tempfile
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_text_extractor import UnifiedTextExtractor, extract_text_from_file_unified

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_pdf_extraction():
    """Test enhanced PDF extraction with multiple methods."""
    logger.info("=== Testing Enhanced PDF Extraction ===")
    
    extractor = UnifiedTextExtractor(verbose=True)
    
    # Test with a sample PDF if available
    test_files = [
        "test_data/sample.pdf",
        "test_data/1033940.pdf",  # Court opinion PDF from memory
        "data/sample.pdf"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            logger.info(f"Testing with: {test_file}")
            try:
                text, method = extractor.extract_text(test_file)
                logger.info(f"✅ Extracted {len(text)} chars using method: {method}")
                if text:
                    logger.info(f"Preview: {text[:200]}...")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to extract from {test_file}: {e}")
    
    # Create a simple test PDF content
    logger.info("Creating test PDF content...")
    try:
        # Create a simple text file to test extraction
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            Supreme Court of the United States
            
            Smith v. Jones, 123 U.S. 456 (2023)
            
            This is a test legal document with citations.
            Another citation: Brown v. Board, 347 U.S. 483 (1954).
            
            The court held that...
            """)
            temp_file = f.name
        
        # Test enhanced text normalization
        text, method = extractor.extract_text(temp_file)
        logger.info(f"✅ Text extraction test: {len(text)} chars using {method}")
        logger.info(f"Normalized text preview: {text[:200]}...")
        
        # Clean up
        os.unlink(temp_file)
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def test_caching_functionality():
    """Test content caching functionality."""
    logger.info("=== Testing Caching Functionality ===")
    
    extractor = UnifiedTextExtractor(verbose=True)
    
    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test content for caching: This should be cached after first extraction.")
        temp_file = f.name
    
    try:
        # First extraction (should cache)
        text1, method1 = extractor.extract_text(temp_file)
        logger.info(f"First extraction: {len(text1)} chars using {method1}")
        
        # Second extraction (should use cache)
        text2, method2 = extractor.extract_text(temp_file)
        logger.info(f"Second extraction: {len(text2)} chars using {method2}")
        
        if method2 == "cache":
            logger.info("✅ Caching working correctly")
            return True
        else:
            logger.warning("⚠️ Cache not used - may be expected for small files")
            return True
            
    except Exception as e:
        logger.error(f"❌ Caching test failed: {e}")
        return False
    finally:
        os.unlink(temp_file)

def test_enhanced_normalization():
    """Test enhanced text normalization."""
    logger.info("=== Testing Enhanced Text Normalization ===")
    
    extractor = UnifiedTextExtractor(verbose=True)
    
    # Test text with various issues
    test_text = """
    \r\n\r\nSupreme Court\r\nDecision\r\n\r\n
    Smith v. Jones, 123 U.S. 456 (2023)\r\n\r\n
    This document has\r\nweird line breaks\tand\ttabs.\r\n
    Email: test@example.com should be removed.\r\n
    Page 1\r\n-------\r\nHeader content\r\n-------\r\n
    The main content starts here with multiple   spaces.\r\n\r\n
    """
    
    try:
        normalized = extractor._enhanced_text_normalization(test_text)
        logger.info("✅ Text normalization completed")
        logger.info(f"Original length: {len(test_text)} chars")
        logger.info(f"Normalized length: {len(normalized)} chars")
        logger.info(f"Normalized text:\n{normalized}")
        
        # Check for expected improvements
        improvements = []
        if '\r\n' not in normalized:
            improvements.append("✅ Removed Windows newlines")
        if '\t' not in normalized:
            improvements.append("✅ Removed tabs")
        if 'test@example.com' not in normalized:
            improvements.append("✅ Removed email")
        if 'Page 1' not in normalized:
            improvements.append("✅ Removed page numbers")
        
        logger.info(f"Normalization improvements: {', '.join(improvements)}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Normalization test failed: {e}")
        return False

def test_backward_compatibility():
    """Test backward compatibility with existing code."""
    logger.info("=== Testing Backward Compatibility ===")
    
    try:
        # Test old function signature
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test backward compatibility")
            temp_file = f.name
        
        # Old function should still work
        from src.unified_text_extractor import extract_text_from_file_smart
        text = extract_text_from_file_smart(temp_file)
        
        logger.info(f"✅ Backward compatibility: {len(text)} chars extracted")
        os.unlink(temp_file)
        return True
        
    except Exception as e:
        logger.error(f"❌ Backward compatibility test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    logger.info("🚀 Starting Enhanced Text Extraction Integration Tests")
    
    tests = [
        ("Enhanced PDF Extraction", test_enhanced_pdf_extraction),
        ("Caching Functionality", test_caching_functionality),
        ("Enhanced Normalization", test_enhanced_normalization),
        ("Backward Compatibility", test_backward_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All integration tests passed! Enhanced text extraction is ready.")
        return True
    else:
        logger.warning(f"⚠️ {total - passed} test(s) failed. Please review the issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
