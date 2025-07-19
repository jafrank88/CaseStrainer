#!/usr/bin/env python3
"""
Test script to verify that the filtering fix is working in the unified workflow.
This tests whether CourtListener results are now being filtered.
"""

import sys
import os
import logging

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_filtering_fix():
    """Test that CourtListener results are now being filtered."""
    
    try:
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        # Create processor instance
        processor = UnifiedCitationProcessorV2()
        
        # Test citations that should be found in CourtListener
        test_citations = [
            "410 U.S. 113",  # Roe v. Wade - definitely in CourtListener
            "347 U.S. 483",  # Brown v. Board - definitely in CourtListener
            "200 Wn.2d 72",  # Washington case - might be in CourtListener
        ]
        
        for test_citation in test_citations:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing citation: {test_citation}")
            logger.info("This citation should be found in CourtListener and filtered if invalid")
            
            # Test the unified workflow
            result = processor.verify_citation_unified_workflow(test_citation)
            
            logger.info(f"Result: {result}")
            
            # Check if filtering worked
            if result.get('verified'):
                canonical_name = result.get('canonical_name')
                verified_by = result.get('verified_by')
                
                logger.info(f"Citation verified by: {verified_by}")
                logger.info(f"Canonical name: {canonical_name}")
                
                # Check if the canonical name is valid
                if canonical_name and processor._is_valid_case_name(canonical_name):
                    logger.info("✓ SUCCESS: Canonical name passed filtering")
                else:
                    logger.warning("✗ FAILURE: Canonical name failed filtering but was still returned")
                    return False
            else:
                logger.info("Citation not verified - this is expected if filtering worked")
                
        return True
            
    except Exception as e:
        logger.error(f"Error testing filtering fix: {e}")
        return False

if __name__ == "__main__":
    success = test_filtering_fix()
    if success:
        print("\n✓ Filtering fix test PASSED")
        sys.exit(0)
    else:
        print("\n✗ Filtering fix test FAILED")
        sys.exit(1) 