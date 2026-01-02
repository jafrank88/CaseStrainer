#!/usr/bin/env python3
"""
Test the verification fixes with the Permian Basin URL
"""

import sys
import os
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_input_processor import UnifiedInputProcessor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_permian_verification_fixes():
    """Test the Permian Basin URL with verification fixes applied."""
    url = "https://www.courtlistener.com/opinion/107672/permian-basin-area-rate-cases/"

    logger.info(f"🔍 Testing Permian Basin URL with verification fixes")
    logger.info(f"URL: {url}")

    try:
        # Initialize the processor
        processor = UnifiedInputProcessor(verbose=True)

        # Process the URL
        logger.info("🚀 Processing URL with UnifiedInputProcessor...")
        start_time = time.time()
        result = processor.process_any_input(url, input_type='url', request_id='test-verification-fixes')
        end_time = time.time()

        processing_time = end_time - start_time
        logger.info(f"📊 Processing completed in {processing_time:.2f} seconds")
        logger.info(f"📊 Processing Results:")
        logger.info(f"  Success: {result.get('success', False)}")
        logger.info(f"  Error: {result.get('error', 'None')}")
        logger.info(f"  Text length: {len(result.get('text', ''))}")
        logger.info(f"  Citations found: {len(result.get('citations', []))}")
        logger.info(f"  Clusters found: {len(result.get('clusters', []))}")

        if result.get('success') and result.get('citations'):
            citations = result.get('citations', [])
            clusters = result.get('clusters', [])
            
            logger.info("✅ SUCCESS: Permian Basin URL processing completed!")
            
            # Analyze verification results
            verified_count = sum(1 for c in citations if c.get('verified', False))
            possible_match_count = sum(1 for c in citations if c.get('possible_match', False))
            total_count = len(citations)
            
            logger.info(f"📚 Citation Analysis:")
            logger.info(f"  Total citations: {total_count}")
            logger.info(f"  Verified: {verified_count} ({verified_count/total_count*100:.1f}%)")
            logger.info(f"  Possible matches: {possible_match_count} ({possible_match_count/total_count*100:.1f}%)")
            logger.info(f"  Unverified: {total_count - verified_count - possible_match_count} ({(total_count - verified_count - possible_match_count)/total_count*100:.1f}%)")
            
            # Check for specific improvements
            logger.info(f"🔍 Verification Fix Analysis:")
            
            # Check OpenJurist improvements
            openjurist_verified = sum(1 for c in citations if c.get('source') == 'OpenJurist' and c.get('verified', False))
            logger.info(f"  OpenJurist verified: {openjurist_verified} (was 0 before fix)")
            
            # Check Google Scholar improvements
            google_scholar_verified = sum(1 for c in citations if c.get('source') == 'Google Scholar' and c.get('verified', False))
            logger.info(f"  Google Scholar verified: {google_scholar_verified} (was 0 before fix)")
            
            # Check for invalid citations being skipped
            invalid_skipped = sum(1 for c in citations if c.get('error') and ('law review' in c.get('error', '').lower() or 'invalid citation' in c.get('error', '').lower()))
            logger.info(f"  Invalid citations properly skipped: {invalid_skipped}")
            
            # Show verification sources used
            sources = set(c.get('source') for c in citations if c.get('source'))
            logger.info(f"  Verification sources used: {', '.join(sorted(sources))}")
            
            # Show some example citations
            logger.info(f"📋 Example Citations:")
            for i, citation in enumerate(citations[:5]):
                status = "✅ VERIFIED" if citation.get('verified', False) else "⚠️ POSSIBLE" if citation.get('possible_match', False) else "❌ UNVERIFIED"
                source = citation.get('source', 'Unknown')
                logger.info(f"  {i+1}. {citation.get('citation', 'N/A')} - {status} ({source})")
            
            # Check if we hit the new timeout targets
            if processing_time < 45:
                logger.info(f"✅ Processing time improved: {processing_time:.2f}s < 45s target")
            else:
                logger.warning(f"⚠️ Processing time still high: {processing_time:.2f}s")
            
            # Calculate overall success rate
            success_rate = (verified_count + possible_match_count) / total_count * 100
            if success_rate >= 80:
                logger.info(f"✅ Success rate target achieved: {success_rate:.1f}% >= 80%")
            else:
                logger.warning(f"⚠️ Success rate below target: {success_rate:.1f}% < 80%")
            
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
    logger.info("🧪 Testing Verification Fixes with Permian Basin URL")
    success = test_permian_verification_fixes()

    if success:
        logger.info("🎉 Verification fixes test PASSED!")
    else:
        logger.error("💥 Verification fixes test FAILED!")

    sys.exit(0 if success else 1)
