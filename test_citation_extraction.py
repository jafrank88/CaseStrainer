#!/usr/bin/env python3
"""
Simple test script to check citation extraction and normalization
"""

import sys
import os
import logging
from src.enhanced_validator_production import extract_text_from_url
from src.citation_processor import CitationProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_citation_extraction(url):
    """Test citation extraction from a URL."""
    print(f"Testing citation extraction from: {url}")
    print("=" * 60)
    
    # Step 1: Extract text from URL
    print("Step 1: Extracting text from URL...")
    try:
        text_result = extract_text_from_url(url)
        if text_result.get('status') != 'success':
            print(f"Error extracting text: {text_result.get('error')}")
            return
        
        extracted_text = text_result.get('text', '')
        print(f"Successfully extracted {len(extracted_text)} characters of text")
        print(f"First 500 characters: {extracted_text[:500]}...")
    except Exception as e:
        print(f"Error extracting text: {e}")
        return
    
    # Step 2: Extract citations
    print("Step 2: Extracting citations...")
    try:
        from src.citation_extractor import extract_all_citations
        citations = extract_all_citations(extracted_text, logger=logger)
        
        print(f"Found {len(citations)} citations:")
        for i, citation_info in enumerate(citations, 1):
            citation = citation_info['citation']
            source = citation_info.get('source', 'unknown')
            print(f"  {i}. {citation} (source: {source})")
        
        # Convert to list of strings for verification
        citation_strings = [citation_info['citation'] for citation_info in citations]
        
    except Exception as e:
        logger.error(f"Error extracting citations: {e}")
        return

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_citation_extraction.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    test_citation_extraction(url) 