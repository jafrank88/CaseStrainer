#!/usr/bin/env python3
"""
Test script for citation processing (synchronous and asynchronous)
"""

import sys
import os
import logging
import asyncio
import json
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional

def setup_logging():
    """Set up logging configuration"""
    log_file = f'test_citation_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Create file handler which logs even debug messages
    fh = logging.FileHandler(log_file, mode='w')
    fh.setLevel(logging.DEBUG)
    
    # Create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return log_file, logger

# Initialize logging
log_file, logger = setup_logger = setup_logging()
logger = logging.getLogger(__name__)

# Sample text with citations for testing
TEST_TEXT = """
A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). 
Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). 
We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003).
See also Smith v. Jones, 100 Wash. 2d 123, 125, 200 P.3d 1 (2001) and Doe v. Roe, 150 Wash. 2d 123, 125, 200 P.3d 1 (2003).
"""

def setup_environment():
    """Set up Python path and import required modules"""
    # Add the src directory to the path
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    if src_dir not in sys.path:
        sys.path.append(src_dir)
    
    try:
        # Import required modules
        from enhanced_sync_processor import EnhancedSyncProcessor, ProcessingOptions
        from config import get_config_value
        
        return {
            'EnhancedSyncProcessor': EnhancedSyncProcessor,
            'ProcessingOptions': ProcessingOptions,
            'get_config_value': get_config_value
        }
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        raise

def test_sync_processing():
    """Test synchronous citation processing"""
    try:
        logger.info("=== Starting Synchronous Processing Test ===")
        
        # Setup environment and get required modules
        modules = setup_environment()
        EnhancedSyncProcessor = modules['EnhancedSyncProcessor']
        ProcessingOptions = modules['ProcessingOptions']
        get_config_value = modules['get_config_value']
        
        # Get API key
        courtlistener_key = get_config_value("COURTLISTENER_API_KEY")
        logger.info(f"CourtListener API key: {'Present' if courtlistener_key else 'Not found'}")
        
        # Initialize processor with verification enabled
        options = ProcessingOptions(
            enable_enhanced_verification=True,
            enable_cross_validation=True,
            enable_false_positive_prevention=True,
            enable_confidence_scoring=True,
            courtlistener_api_key=courtlistener_key
        )
        
        logger.info("Creating EnhancedSyncProcessor instance...")
        processor = EnhancedSyncProcessor(options=options)
        
        # Process text synchronously
        logger.info("Processing text synchronously...")
        start_time = datetime.now()
        
        # Process the text using the enhanced processor
        result = processor.process_any_input_enhanced(TEST_TEXT, input_type='text')
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Log results
        logger.info(f"Synchronous processing completed in {processing_time:.2f} seconds")
        logger.info(f"Found {len(result.get('citations', []))} citations")
        
        # Save results to file
        with open('sync_processing_results.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info("Results saved to sync_processing_results.json")
        return result
        
    except Exception as e:
        logger.error(f"Error in test_sync_processing: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        # Log Python version and environment info
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Python path: {sys.path}")
        logger.info(f"Logging to file: {os.path.abspath(log_file)}")
        
        # Test synchronous processing
        logger.info("\n=== Testing Synchronous Processing ===")
        result = test_sync_processing()
        
        logger.info("\n=== Test completed successfully ===")
        logger.info(f"Found {len(result.get('citations', []))} citations in the test text.")
        
    except Exception as e:
        logger.error("\n=== Test Failed ===")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
