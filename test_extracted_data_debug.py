import asyncio
import sys
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_extracted_data_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

async def test_extracted_data():
    try:
        logger.info("Starting test_extracted_data")
        
        # Import inside the function to catch import errors
        try:
            from unified_citation_processor_v2 import UnifiedCitationProcessorV2
            logger.info("Successfully imported UnifiedCitationProcessorV2")
        except Exception as e:
            logger.error(f"Failed to import UnifiedCitationProcessorV2: {e}")
            raise
        
        try:
            logger.info("Creating processor instance")
            processor = UnifiedCitationProcessorV2()
            logger.info("Processor instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create processor: {e}")
            raise

        # Test with a simple text containing known citations
        test_text = """
        In State v. Smith, 123 Wash. 2d 1, 864 P.2d 87 (1993), the court held that...
        See also 536 P.3d 191 (Wash. 2023) and 169 Wn.2d 815, 239 P.3d 354 (2010).
        """
        
        logger.info("Processing test text")
        try:
            results = await processor.process_document_citations(test_text)
            logger.info("Successfully processed document citations")
        except Exception as e:
            logger.error(f"Error in process_document_citations: {e}")
            raise

        # Print results
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        
        # Print citations
        print("\nCITATIONS:")
        print("-"*40)
        citations = results.get('citations', [])
        print(f"Found {len(citations)} citations")
        
        for i, citation in enumerate(citations, 1):
            print(f"\nCitation {i}:")
            print(f"  - Type: {type(citation).__name__}")
            
            if hasattr(citation, '__dict__'):
                print("  - Available attributes:", ', '.join([k for k in dir(citation) if not k.startswith('_')]))
            
            if isinstance(citation, dict):
                print("  - Dictionary keys:", ', '.join(citation.keys()))
            
            print(f"  - Full Citation: {getattr(citation, 'citation', str(citation))}")
            print(f"  - Extracted Case Name: {getattr(citation, 'extracted_case_name', 'N/A')}")
            print(f"  - Extracted Date: {getattr(citation, 'extracted_date', 'N/A')}")
            print(f"  - Canonical Name: {getattr(citation, 'canonical_name', 'N/A')}")
            print(f"  - Canonical Date: {getattr(citation, 'canonical_date', 'N/A')}")
    
    except Exception as e:
        logger.exception("Test failed with exception")
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting test with detailed debugging...")
    asyncio.run(test_extracted_data())
