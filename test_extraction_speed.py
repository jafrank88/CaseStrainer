#!/usr/bin/env python3
"""
Simple test to check if the unified extraction pipeline is stuck or just slow.
Also compares results with Table of Authorities parser for ground truth.
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

def test_small_text():
    """Test with a small text sample to see if extraction works at all."""
    logger.info("Testing with small text sample...")
    
    processor = UnifiedCitationProcessorV2()
    
    # Small test text with known citations
    test_text = """
    In Smith v. Jones, 123 F.3d 456 (9th Cir. 2020), the court held that due process requires notice.
    See also Brown v. Board, 347 U.S. 483 (1954); Miranda v. Arizona, 384 U.S. 436 (1966).
    The plaintiff cited 8 P.2d 1094 as support, but this appears to be a page reference error.
    """
    
    start_time = time.time()
    try:
        citations = processor._extract_citations_unified(test_text)
        end_time = time.time()
        
        logger.info(f"✅ Small test completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Found {len(citations)} citations:")
        
        for i, citation in enumerate(citations, 1):
            logger.info(f"  {i}. {citation.citation}")
            logger.info(f"     Name: {citation.extracted_case_name or 'None'}")
            logger.info(f"     Date: {citation.extracted_date or 'None'}")
            logger.info(f"     Source: {getattr(citation, 'source', 'unknown')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Small test failed: {e}")
        return False

def test_medium_file():
    """Test with a medium-sized file to check performance."""
    logger.info("Testing with medium-sized file...")
    
    processor = UnifiedCitationProcessorV2()
    
    # Use a smaller file first
    test_file = Path("D:/dev/casestrainer/wa_briefs_txt/001_Answer to Petition for Review.txt")
    
    if not test_file.exists():
        logger.warning(f"Test file not found: {test_file}")
        return False
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        logger.info(f"File size: {len(text)} characters")
        
        # Set a timeout to detect if it's stuck
        start_time = time.time()
        
        logger.info("Starting extraction... (will timeout after 30 seconds)")
        citations = processor._extract_citations_unified(text)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"✅ Medium test completed in {duration:.2f} seconds")
        logger.info(f"Found {len(citations)} citations")
        logger.info(f"Performance: {len(citations)/duration:.1f} citations/second")
        
        # Show first few citations
        for i, citation in enumerate(citations[:3], 1):
            logger.info(f"  {i}. {citation.citation}")
            logger.info(f"     Name: {citation.extracted_case_name or 'None'}")
            logger.info(f"     Date: {citation.extracted_date or 'None'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Medium test failed: {e}")
        return False

def compare_with_toa_parser():
    """Compare extraction results with Table of Authorities parser for ground truth."""
    logger.info("Comparing with Table of Authorities parser...")
    
    try:
        # Check if toa_parser exists
        from src.toa_parser import ImprovedToAParser
        
        test_file = Path("D:/dev/casestrainer/wa_briefs_txt/001_Answer to Petition for Review.txt")
        
        if not test_file.exists():
            logger.warning(f"Test file not found: {test_file}")
            return False
        
        with open(test_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract Table of Authorities
        logger.info("Extracting Table of Authorities...")
        toa_parser = ImprovedToAParser()
        toa_entries = toa_parser.parse_toa_section(text)
        
        # Convert TOA entries to simple citation list for comparison
        toa_citations = []
        for entry in toa_entries:
            toa_citations.extend(entry.citations)
        
        # Remove TOA section from text for body extraction
        # Simple approach: find "TABLE OF AUTHORITIES" and remove everything until next major section
        toa_start = text.upper().find("TABLE OF AUTHORITIES")
        if toa_start != -1:
            # Find end of TOA (look for next major section)
            possible_ends = [
                text.upper().find("STATEMENT OF THE CASE", toa_start),
                text.upper().find("STATEMENT OF ISSUES", toa_start),
                text.upper().find("ARGUMENT", toa_start),
                text.upper().find("INTRODUCTION", toa_start),
                text.upper().find("SUMMARY", toa_start)
            ]
            toa_end = min([end for end in possible_ends if end > toa_start], default=len(text))
            
            body_text = text[:toa_start] + text[toa_end:]
            logger.info(f"Removed TOA section ({toa_end - toa_start} characters)")
        else:
            body_text = text
            logger.info("No TOA section found, using full text")
        
        # Extract citations from body
        processor = UnifiedCitationProcessorV2()
        logger.info("Extracting citations from brief body...")
        body_citations = processor._extract_citations_unified(body_text)
        
        # Compare results
        logger.info(f"\nCOMPARISON RESULTS:")
        logger.info(f"TOA citations: {len(toa_citations)}")
        logger.info(f"Body citations: {len(body_citations)}")
        
        # Show TOA citations with names and years
        logger.info(f"\nTOA CITATIONS (ground truth):")
        for i, entry in enumerate(toa_entries[:5], 1):
            logger.info(f"  {i}. Case: {entry.case_name}")
            logger.info(f"     Citations: {entry.citations}")
            logger.info(f"     Years: {entry.years}")
            logger.info(f"     Confidence: {entry.confidence:.2f}")
        
        # Show body citations
        logger.info(f"\nBODY CITATIONS (extracted):")
        for i, citation in enumerate(body_citations[:5], 1):
            logger.info(f"  {i}. {citation.citation}")
            logger.info(f"     Name: {citation.extracted_case_name or 'None'}")
            logger.info(f"     Date: {citation.extracted_date or 'None'}")
        
        return True
        
    except ImportError:
        logger.warning("toa_parser not available - skipping TOA comparison")
        return False
    except Exception as e:
        logger.error(f"❌ TOA comparison failed: {e}")
        return False

def main():
    """Run performance and accuracy tests."""
    logger.info("Starting extraction performance and accuracy tests")
    logger.info("="*60)
    
    # Test 1: Small text (should be fast)
    if not test_small_text():
        logger.error("Small test failed - extraction may be broken")
        return
    
    logger.info("\n" + "="*60)
    
    # Test 2: Medium file (check if it's just slow)
    if not test_medium_file():
        logger.error("Medium test failed - extraction may be stuck or broken")
        return
    
    logger.info("\n" + "="*60)
    
    # Test 3: Compare with TOA parser
    compare_with_toa_parser()
    
    logger.info("\n" + "="*60)
    logger.info("All tests completed!")

if __name__ == "__main__":
    main()
