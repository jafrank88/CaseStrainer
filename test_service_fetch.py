#!/usr/bin/env python3
"""
Test the citation_service._fetch_url_content method to confirm the size limit issue
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api.services.citation_service import CitationService
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_service_fetch():
    """Test CitationService._fetch_url_content with the Justia URL."""
    url = "https://law.justia.com/cases/federal/us/390/747/"
    
    logger.info(f"Testing CitationService._fetch_url_content with: {url}")
    
    service = CitationService()
    
    try:
        content = service._fetch_url_content(url)
        
        logger.info(f"Return type: {type(content)}")
        logger.info(f"Content is None: {content is None}")
        
        if content:
            logger.info(f"Content length: {len(content)}")
            logger.info(f"Content strip length: {len(content.strip())}")
            logger.info(f"Content preview: {content[:200]}...")
        else:
            logger.error("❌ No content returned - likely due to size limit")
            
    except Exception as e:
        logger.error(f"❌ Exception in _fetch_url_content: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service_fetch()
