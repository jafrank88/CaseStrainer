#!/usr/bin/env python3
"""
Test fetch_url_content function directly to debug the issue
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.progress_manager import fetch_url_content
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fetch_direct():
    """Test fetch_url_content directly with the Justia URL."""
    url = "https://law.justia.com/cases/federal/us/390/747/"
    
    logger.info(f"Testing fetch_url_content with: {url}")
    
    try:
        content = fetch_url_content(url)
        
        logger.info(f"Return type: {type(content)}")
        logger.info(f"Content length: {len(content) if content else 0}")
        logger.info(f"Content is None: {content is None}")
        logger.info(f"Content is empty string: {content == ''}")
        
        if content:
            logger.info(f"Content strip length: {len(content.strip())}")
            logger.info(f"Content preview: {content[:200]}...")
            
            # Check if it meets the threshold
            if len(content.strip()) >= 10:
                logger.info("✅ Content meets minimum threshold")
            else:
                logger.error(f"❌ Content too short: {len(content.strip())} < 10")
        else:
            logger.error("❌ No content returned")
            
    except Exception as e:
        logger.error(f"❌ Exception in fetch_url_content: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fetch_direct()
