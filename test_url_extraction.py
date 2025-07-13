#!/usr/bin/env python3
"""
Test script to verify URL extraction for the specific PDF that failed.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from document_processing_unified import UnifiedDocumentProcessor
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_url_extraction():
    """Test URL extraction for the specific PDF that failed."""
    url = "https://www.courts.wa.gov/opinions/pdf/868381.pdf"
    
    print(f"Testing URL extraction for: {url}")
    
    try:
        # Create processor
        processor = UnifiedDocumentProcessor()
        
        # Extract text from URL
        print("Extracting text from URL...")
        text = processor.extract_text_from_url(url)
        
        print(f"Successfully extracted {len(text)} characters")
        print(f"First 500 characters: {text[:500]}")
        print(f"Last 500 characters: {text[-500:]}")
        
        # Check if text contains any citations
        citation_indicators = ['v.', 'v ', 'In re', 'State v.', 'United States v.']
        found_indicators = []
        for indicator in citation_indicators:
            if indicator in text:
                found_indicators.append(indicator)
        
        print(f"Citation indicators found: {found_indicators}")
        
        # Try to extract citations
        print("\nTesting citation extraction...")
        result = processor.process_document(url=url, extract_case_names=True, debug_mode=True)
        
        print(f"Processing result: {result}")
        
        citations = result.get('citations', [])
        print(f"Found {len(citations)} citations")
        
        for i, citation in enumerate(citations[:5]):  # Show first 5
            print(f"Citation {i+1}: {citation}")
        
        return True
        
    except Exception as e:
        print(f"Error during URL extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_url_extraction()
    if success:
        print("\n✅ URL extraction test completed successfully")
    else:
        print("\n❌ URL extraction test failed")
        sys.exit(1) 