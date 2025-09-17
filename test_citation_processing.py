#!/usr/bin/env python3
"""
Test script for citation processing (synchronous and asynchronous)
"""

import sys
import os
import logging
import asyncio
import json
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
log_file, logger = setup_logging()

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
        from async_verification_worker import verify_citations_async, verify_citations_enhanced
        from config import get_config_value
        
        return {
            'EnhancedSyncProcessor': EnhancedSyncProcessor,
            'ProcessingOptions': ProcessingOptions,
            'verify_citations_async': verify_citations_async,
            'verify_citations_enhanced': verify_citations_enhanced,
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
        logger.error(f"Synchronous processing test failed: {str(e)}", exc_info=True)
        raise

async def test_async_processing():
    """Test asynchronous citation processing"""
    try:
        logger.info("\n=== Starting Asynchronous Processing Test ===")
        
        # Setup environment and get required modules
        modules = setup_environment()
        verify_citations_async = modules['verify_citations_async']
        verify_citations_enhanced = modules['verify_citations_enhanced']
        
        # First, extract citations synchronously
        from unified_citation_processor import UnifiedCitationProcessor
        processor = UnifiedCitationProcessor()
        
        logger.info("Extracting citations...")
        citations = processor.extract_citations(TEST_TEXT)
        
        if not citations:
            logger.warning("No citations found in test text")
            return None
            
        logger.info(f"Found {len(citations)} citations to verify asynchronously")
        
        # Test basic async verification
        logger.info("Starting basic async verification...")
        start_time = datetime.now()
        
        basic_result = await verify_citations_async(
            citations=citations,
            text=TEST_TEXT,
            request_id="test_async_1",
            input_type="text",
            metadata={"test": True}
        )
        
        basic_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Basic async verification completed in {basic_time:.2f} seconds")
        
        # Test enhanced async verification
        logger.info("Starting enhanced async verification...")
        start_time = datetime.now()
        
        enhanced_result = await verify_citations_enhanced(
            citations=citations,
            text=TEST_TEXT,
            request_id="test_async_2",
            input_type="text",
            metadata={"test": True}
        )
        
        enhanced_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Enhanced async verification completed in {enhanced_time:.2f} seconds")
        
        # Save results
        results = {
            'basic_verification': {
                'time_seconds': basic_time,
                'citations_processed': len(citations),
                'result': basic_result
            },
            'enhanced_verification': {
                'time_seconds': enhanced_time,
                'citations_processed': len(citations),
                'result': enhanced_result
            }
        }
        
        with open('async_processing_results.json', 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info("Async processing results saved to async_processing_results.json")
        return results
        
    except Exception as e:
        logger.error(f"Asynchronous processing test failed: {str(e)}", exc_info=True)
        raise
        
        # Process the text through the full pipeline
        logger.info("Starting text processing...")
        logger.info(f"Input text length: {len(test_text)} characters")
        
        # Log the first 200 characters of the input text
        logger.info(f"Sample input text: {test_text[:200]}...")
        
        # Process the text
        result = processor.process_any_input_enhanced(
            input_data=test_text,
            input_type="text",
            options={"request_id": "test_123"}
        )
        
        # Display results in a more readable format
        print("\n" + "="*80)
        print("CITATION PROCESSING RESULTS")
        print("="*80)
        
        print(f"\nResult type: {type(result).__name__}")
        
        if isinstance(result, dict):
            print(f"\nResult keys: {list(result.keys())}")
            
            if 'citations' in result and result['citations']:
                print(f"\nFound {len(result['citations'])} citations:")
                print("-"*60)
                
                for i, citation in enumerate(result['citations'], 1):
                    print(f"\nCITATION {i}:")
                    print("-"*40)
                    
                    # Handle different citation formats
                    if hasattr(citation, 'to_dict'):
                        citation_data = citation.to_dict()
                    elif isinstance(citation, dict):
                        citation_data = citation
                    else:
                        print(f"  [Unsupported citation type: {type(citation).__name__}]")
                        print(f"  {citation}")
                        continue
                    
                    # Display common citation fields
                    for key in ['citation', 'case_name', 'year', 'volume', 'reporter', 'page', 'url']:
                        if key in citation_data and citation_data[key]:
                            print(f"  {key}: {citation_data[key]}")
                    
                    # Display any metadata
                    if 'metadata' in citation_data and citation_data['metadata']:
                        print("  metadata:")
                        for k, v in citation_data['metadata'].items():
                            print(f"    {k}: {v}")
                    
                    # Display any additional fields
                    other_fields = set(citation_data.keys()) - {'citation', 'case_name', 'year', 'volume', 'reporter', 'page', 'url', 'metadata'}
                    for field in other_fields:
                        if citation_data[field]:  # Only show non-empty fields
                            print(f"  {field}: {citation_data[field]}")
            else:
                print("\nNo citations found in the result.")
                if 'error' in result:
                    print(f"Error: {result['error']}")
                
            # Log the full result for debugging
            logger.debug("\nFull result object:")
            logger.debug(result)
        else:
            print(f"\nUnexpected result type: {type(result).__name__}")
            print(f"Result: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in test_citation_processing: {str(e)}", exc_info=True)
        raise

def setup_logging():
    """Set up logging configuration"""
if __name__ == "__main__":
    # Set up logging to file and console
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Logging to file: {os.path.abspath(log_file)}")
    
    try:
        # Test synchronous processing
        logger.info("\n=== Testing Synchronous Processing ===")
        test_sync_processing()
        
        # Test asynchronous processing
        logger.info("\n=== Testing Asynchronous Processing ===")
        test_async_processing()
        
        logger.info("\n=== All tests completed successfully ===")
    except Exception as e:
        logger.error("=== Test Failed ===")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
