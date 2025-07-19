#!/usr/bin/env python3
"""
Script to clear the cache and test the filtering logic.
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

def clear_cache_and_test():
    """Clear the cache and test the filtering logic."""
    
    try:
        from src.canonical_case_name_service import CanonicalCaseNameService, get_canonical_case_name_with_date
        
        # Create a new service instance to clear the cache
        service = CanonicalCaseNameService()
        
        # Clear the LRU cache by accessing it directly
        if hasattr(service, '_cached_lookup'):
            service._cached_lookup.cache_clear()
            logger.info("✓ Cleared LRU cache")
        
        # Test with a citation that should trigger filtering
        test_citation = "410 U.S. 113"
        
        logger.info(f"Testing citation: {test_citation}")
        logger.info("This should trigger the filtering logic and reject web domains")
        
        # Test the canonical lookup
        result = get_canonical_case_name_with_date(test_citation)
        
        logger.info(f"Result: {result}")
        
        if result:
            case_name = result.get('case_name')
            if case_name:
                # Check if it's a web domain
                if any(domain in case_name.lower() for domain in ['youtube.com', 'google.com', 'cheaperthandirt.com', 'http', 'www.']):
                    logger.warning("✗ FAILURE: Web domain still returned as canonical name")
                    return False
                else:
                    logger.info("✓ SUCCESS: Valid canonical name returned")
                    return True
            else:
                logger.info("✓ SUCCESS: No canonical name returned (filtering worked)")
                return True
        else:
            logger.info("✓ SUCCESS: No result returned (filtering worked)")
            return True
            
    except Exception as e:
        logger.error(f"Error testing cache clearing: {e}")
        return False

if __name__ == "__main__":
    success = clear_cache_and_test()
    if success:
        print("\n✓ Cache clearing and filtering test PASSED")
        sys.exit(0)
    else:
        print("\n✗ Cache clearing and filtering test FAILED")
        sys.exit(1) 