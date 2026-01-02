#!/usr/bin/env python3
"""
Test URL fetching to debug the Permian Basin URL issue
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.progress_manager import fetch_url_content
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_url_fetch():
    """Test fetching the problematic URL."""
    url = "https://www.courtlistener.com/opinion/107672/permian-basin-area-rate-cases/"
    
    logger.info(f"Testing URL: {url}")
    
    try:
        content = fetch_url_content(url)
        
        if content:
            logger.info(f"✅ Successfully fetched {len(content)} characters")
            logger.info(f"Content preview: {content[:500]}...")
            
            # Check for legal citations in the content
            import re
            citation_patterns = [
                r'\d+\s+F\.\d+\s+\d+',  # Federal citations
                r'\d+\s+U\.\S\.\s+\d+',  # US citations
                r'\d+\s+S\. Ct\.\s+\d+',  # Supreme Court citations
                r'\d+\s+L\. Ed\.\s+\d+',  # Lawyer's Edition citations
            ]
            
            citations_found = []
            for pattern in citation_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                citations_found.extend(matches)
            
            if citations_found:
                logger.info(f"Found {len(citations_found)} potential citations:")
                for citation in citations_found[:10]:  # Show first 10
                    logger.info(f"  - {citation}")
            else:
                logger.warning("No citations found in the content")
                
            return True
        else:
            logger.error("❌ No content returned from URL")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error fetching URL: {str(e)}")
        return False

def test_url_with_different_methods():
    """Test URL with different fetching methods."""
    url = "https://www.courtlistener.com/opinion/107672/permian-basin-area-rate-cases/"
    
    logger.info("=== Testing with different methods ===")
    
    # Method 1: Using requests directly
    try:
        import requests
        response = requests.get(url, timeout=30)
        logger.info(f"Requests method: Status {response.status_code}, Content-Length {len(response.text)}")
        if response.text:
            logger.info(f"Requests preview: {response.text[:200]}...")
    except Exception as e:
        logger.error(f"Requests method failed: {e}")
    
    # Method 2: Using the existing fetch_url_content
    try:
        content = fetch_url_content(url)
        logger.info(f"fetch_url_content method: {len(content) if content else 0} characters")
        if content:
            logger.info(f"fetch_url_content preview: {content[:200]}...")
    except Exception as e:
        logger.error(f"fetch_url_content method failed: {e}")

if __name__ == "__main__":
    logger.info("🔍 Testing URL fetching for Permian Basin case")
    
    # Test basic fetching
    success = test_url_fetch()
    
    # Test with different methods
    test_url_with_different_methods()
    
    if success:
        logger.info("✅ URL fetching test completed successfully")
    else:
        logger.error("❌ URL fetching test failed")
    
    sys.exit(0 if success else 1)
