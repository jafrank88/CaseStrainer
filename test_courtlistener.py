#!/usr/bin/env python3
"""
Test script for CourtListener API integration.

This script tests the citation verification functionality with the CourtListener API.
It loads the API key from config.json and tests a few sample citations.
"""

import json
import os
import sys
import logging
from typing import Dict, Any, Optional
import requests
from citation_verification import CitationVerifier

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
CONFIG_FILE = 'config.json'
TEST_CITATIONS = [
    "505 U.S. 1003",  # Known good Supreme Court case
    "999 F.3d 1234",  # Federal Reporter case (likely doesn't exist)
    "123 S. Ct. 456",  # Supreme Court Reporter
    "789 F.2d 123",   # Federal Reporter 2nd Series
    "456 F. Supp. 3d 123",  # Federal Supplement
]

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {CONFIG_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        sys.exit(1)

def test_courtlistener_api(api_key: str):
    """Test the CourtListener API integration."""
    logger.info("Testing CourtListener API integration...")
    
    try:
        # Initialize the verifier with debug mode on
        verifier = CitationVerifier(api_key=api_key, debug_mode=True)
        logger.info("Successfully initialized CitationVerifier")
        
        # Test each citation
        for citation in TEST_CITATIONS:
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing citation: {citation}")
            logger.info("-" * 50)
            
            try:
                # Format the citation for CourtListener
                logger.info("Formatting citation...")
                formatted_citation = verifier._format_citation_for_courtlistener(citation)
                logger.info(f"Formatted citation: {formatted_citation}")
                
                # Verify the citation
                logger.info("Verifying citation with CourtListener API...")
                result = verifier.verify_with_courtlistener_citation_api(citation)
                
                # Print the result
                logger.info(f"\nVerification result for '{citation}':")
                logger.info(f"  Found: {result.get('found', False)}")
                logger.info(f"  Valid: {result.get('valid', False)}")
                logger.info(f"  Status: {result.get('status', 'N/A')}")
                logger.info(f"  Case Name: {result.get('case_name', 'N/A')}")
                logger.info(f"  URL: {result.get('url', 'N/A')}")
                logger.info(f"  Explanation: {result.get('explanation', 'N/A')}")
                
                if 'error_message' in result and result['error_message']:
                    logger.warning(f"  Error: {result['error_message']}")
                    
                if 'details' in result and result['details']:
                    logger.info("  Details:")
                    for key, value in result['details'].items():
                        logger.info(f"    {key}: {value}")
                        
            except Exception as e:
                logger.error(f"Error testing citation '{citation}': {str(e)}", exc_info=True)
                logger.error("Continuing with next citation...")
                continue
                
    except Exception as e:
        logger.error(f"Fatal error in test_courtlistener_api: {str(e)}", exc_info=True)
        raise

def main():
    """Main function."""
    try:
        logger.info("Starting CourtListener API test script")
        
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Get API key (try both possible key names)
        api_key = config.get('COURTLISTENER_API_KEY') or config.get('courtlistener_api_key')
        if not api_key:
            error_msg = "No CourtListener API key found in config.json"
            logger.error(error_msg)
            logger.error("Please add your API key to config.json with key 'COURTLISTENER_API_KEY' or 'courtlistener_api_key'")
            sys.exit(1)
        
        logger.info(f"Successfully retrieved API key (first 6 chars: {api_key[:6]}...)")
        
        # Test the API
        logger.info("Starting API tests...")
        test_courtlistener_api(api_key)
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {str(e)}", exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test script interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
