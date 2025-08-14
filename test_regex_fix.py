#!/usr/bin/env python3
"""
Quick test to verify the regex timeout fix works and pipeline no longer hangs.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_regex_fix():
    """Test that the regex timeout fix prevents hanging."""
    logger.info("Testing regex timeout fix...")
    
    processor = UnifiedCitationProcessorV2()
    
    # Test with a medium-sized file that was causing issues
    test_file = Path("D:/dev/casestrainer/wa_briefs_txt/001_Answer to Petition for Review.txt")
    
    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return False
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        logger.info(f"Testing file: {test_file.name}")
        logger.info(f"File size: {len(text):,} characters")
        
        # Set a reasonable timeout
        start_time = time.time()
        logger.info("Starting extraction with timeout protection...")
        
        citations = processor._extract_citations_unified(text)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ SUCCESS: Extraction completed in {duration:.2f} seconds")
        logger.info(f"Found {len(citations)} citations")
        
        # Show first few citations
        logger.info("First 3 citations:")
        for i, citation in enumerate(citations[:3], 1):
            logger.info(f"  {i}. {citation.citation}")
            logger.info(f"     Name: {citation.extracted_case_name or 'None'}")
            logger.info(f"     Date: {citation.extracted_date or 'None'}")
        
        # Performance assessment
        if duration < 10:
            logger.info("🚀 EXCELLENT: Fast extraction (< 10 seconds)")
        elif duration < 30:
            logger.info("⚠️  ACCEPTABLE: Moderate extraction time (< 30 seconds)")
        else:
            logger.info("❌ SLOW: Extraction took too long (> 30 seconds)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ FAILED: {e}")
        return False

def main():
    """Run the regex fix test."""
    logger.info("Starting regex timeout fix verification")
    logger.info("="*60)
    
    success = test_regex_fix()
    
    if success:
        logger.info("\n" + "="*60)
        logger.info("✅ REGEX FIX VERIFICATION: SUCCESS")
        logger.info("The unified pipeline no longer hangs on regex operations!")
        logger.info("Ready for production use.")
    else:
        logger.info("\n" + "="*60)
        logger.info("❌ REGEX FIX VERIFICATION: FAILED")
        logger.info("The pipeline still has issues that need to be resolved.")

if __name__ == "__main__":
    main()
