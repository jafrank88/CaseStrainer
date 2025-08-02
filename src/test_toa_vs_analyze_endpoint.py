#!/usr/bin/env python3
"""
Compare ToA parser vs unified citation processor on ToA lines.
Test how each tool extracts case names and dates from the same ToA text.
"""

import logging
logger = logging.getLogger(__name__)

from src.toa_parser import ImprovedToAParser
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

def test_toa_line_comparison():
    """Test extraction on sample ToA lines."""
    
    # Sample ToA lines from the brief
    toa_lines = [
        "In re Det. of Pouncy, 168 Wn.2d 382,229 P.3d 678 (2010) ..................... 17",
        "Jones v. Hogan, 56 Wn.2d 23,351 P.2d 153 (1960) ................................. 24",
        "State v. Boehning, 127 Wn. App. 511, 111 P.3d 899 (2005) ..................... 23",
        "State v. Bradley, 141 Wn.2d 731, 10 P.3d 358 (2000) ............................. 23",
        "State v. Brett, 126 Wn.2d 136, 892 P.2d 29 (1995) ............................... 23"
    ]
    
    # Initialize processors
    toa_parser = ImprovedToAParser()
    citation_processor = UnifiedCitationProcessorV2()
    
    logger.info("COMPARISON: ToA Parser vs Unified Citation Processor")
    logger.info("=" * 80)
    
    for i, line in enumerate(toa_lines, 1):
        logger.info(f"\n{i}. TESTING LINE: {line}")
        logger.info("-" * 60)
        
        # Test with ToA Parser
        logger.info("TOA PARSER RESULTS:")
        toa_entry = toa_parser._parse_chunk_flexible(line)
        if toa_entry:
            logger.info(f"  Case Name: {getattr(toa_entry, 'case_name', 'None')}")
            logger.info(f"  Citations: {getattr(toa_entry, 'citations', 'None')}")
            logger.info(f"  Years: {getattr(toa_entry, 'years', 'None')}")
        else:
            logger.info("  No ToA entry parsed")
        
        # Test with Unified Citation Processor
        logger.info("\nUNIFIED CITATION PROCESSOR RESULTS:")
        try:
            # Clean the line for the citation processor (remove page indicators)
            clean_line = line.split('.....................')[0].strip()
            
            # Import asyncio for running the async function
            import asyncio
            
            # Run the async process_text function
            results = asyncio.run(citation_processor.process_text(clean_line))
            
            if results and isinstance(results, dict) and results.get('citations'):
                for j, citation in enumerate(results['citations']):
                    logger.info(f"  Citation {j+1}:")
                    logger.info(f"    Extracted Name: {citation.get('extracted_case_name', 'None')}")
                    logger.info(f"    Extracted Date: {citation.get('extracted_date', 'None')}")
                    logger.info(f"    Canonical Name: {citation.get('canonical_name', 'None')}")
                    logger.info(f"    Canonical Date: {citation.get('canonical_date', 'None')}")
            else:
                logger.info("  No citations extracted")
        except Exception as e:
            logger.error(f"  Error: {e}")
        
        logger.info("")  # Empty line for readability

if __name__ == "__main__":
    test_toa_line_comparison() 