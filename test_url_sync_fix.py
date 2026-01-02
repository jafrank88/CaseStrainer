#!/usr/bin/env python3
"""
Test if URL sync mode fix is working
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api.services.citation_service import CitationService

def test_url_sync_fix():
    """Test if URLs now process synchronously"""
    
    service = CitationService()
    
    # Test URL input data
    url_input = {'type': 'url', 'url': 'https://supreme.justia.com/cases/federal/us/390/747/'}
    
    print(f"Testing URL sync routing...")
    print(f"Input: {url_input}")
    
    # Test should_process_immediately with force_mode='sync'
    should_process = service.should_process_immediately(url_input, force_mode='sync')
    
    print(f"Should process immediately with force_mode='sync': {should_process}")
    
    if should_process:
        print("[SUCCESS] SUCCESS: URL will now process synchronously")
    else:
        print("[ERROR] FAILED: URL still routes to async")
    
    # Test without force_mode
    should_process_default = service.should_process_immediately(url_input)
    print(f"Should process immediately without force_mode: {should_process_default}")
    
    # Test the actual text extraction
    extracted_text = service.extract_text_from_input(url_input)
    if extracted_text:
        print(f"Extracted text size: {len(extracted_text)} characters")
        print(f"Sync threshold: {service.SYNC_THRESHOLD} bytes")
        
        if len(extracted_text.encode('utf-8')) < service.SYNC_THRESHOLD:
            print("[SUCCESS] Would be sync even without force_mode")
        else:
            print("[INFO] Would be async without force_mode (too large)")
            print("[SUCCESS] But force_mode='sync' overrides this")

if __name__ == "__main__":
    test_url_sync_fix()
