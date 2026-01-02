#!/usr/bin/env python3
"""
Test the Permian Basin URL fix end-to-end
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_input_processor import UnifiedInputProcessor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_permian_url_fix():
    """Test the Permian Basin URL fix with the actual processor."""
    url = "https://www.courtlistener.com/opinion/107672/permian-basin-area-rate-cases/"
    
    logger.info(f"🔍 Testing Permian Basin URL fix")
    logger.info(f"URL: {url}")
    
    try:
        # Initialize the processor
        processor = UnifiedInputProcessor(verbose=True)
        
        # Process the URL
        logger.info("🚀 Processing URL with UnifiedInputProcessor...")
        result = processor.process_any_input(url, input_type='url', request_id='test-permian-fix')
        
        logger.info("📊 Processing Results:")
        logger.info(f"  Success: {result.get('success', False)}")
        logger.info(f"  Error: {result.get('error', 'None')}")
        logger.info(f"  Text length: {len(result.get('text', ''))}")
        logger.info(f"  Citations found: {len(result.get('citations', []))}")
        logger.info(f"  Metadata: {result.get('metadata', {})}")
        
        if result.get('success') and result.get('text'):
            logger.info("✅ SUCCESS: Permian Basin URL processing completed!")
            logger.info(f"Text preview: {result['text'][:300]}...")
            
            citations = result.get('citations', [])
            if citations:
                logger.info(f"📋 Found {len(citations)} citations:")
                for i, citation in enumerate(citations[:5]):  # Show first 5
                    logger.info(f"  {i+1}. {citation}")
            else:
                logger.warning("⚠️ No citations found in the processed text")
                
            return True
        else:
            error = result.get('error', 'Unknown error')
            logger.error(f"❌ FAILED: {error}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Exception during processing: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing Permian Basin URL Fix")
    success = test_permian_url_fix()
    
    if success:
        logger.info("🎉 Permian Basin URL fix test PASSED!")
    else:
        logger.error("💥 Permian Basin URL fix test FAILED!")
    
    sys.exit(0 if success else 1)
