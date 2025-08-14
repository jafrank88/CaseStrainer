"""
Direct test of the citation processor with sample text.
This bypasses the service layer and tests the core functionality directly.
"""
import sys
import logging
from typing import List, Dict, Any

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock environment variables to avoid loading from .env file
import os
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['COURTLISTENER_API_KEY'] = 'test-key'  # Mock API key for testing

def test_citation_processing():
    """Test citation processing with sample text directly using the processor."""
    # Set up logging first
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('test_citation_processor')
    
    # Sample legal text with citations
    sample_text = """
    In Luis v. United States, 578 U.S. 5 (2016), the Supreme Court held that 
    a pretrial freeze of untainted assets violates a defendant's Sixth Amendment 
    right to counsel of choice. This decision was later cited in United States 
    v. Jones, 950 F.3d 1106 (9th Cir. 2020), where the court further clarified 
    the scope of this protection. Additionally, the case of Carpenter v. United States, 
    138 S. Ct. 2206 (2018) addressed Fourth Amendment issues in the digital age.
    """
    
    try:
        logger.info("Importing UnifiedCitationProcessorV2...")
        from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        logger.info("Initializing processor...")
        processor = UnifiedCitationProcessorV2()
        
        logger.info("Extracting citations...")
        try:
            # Set up processor-specific logging
            proc_logger = logging.getLogger('unified_processor')
            proc_logger.setLevel(logging.DEBUG)
            
            logger.info("Calling _extract_citations_unified...")
            
            # Add timeout to prevent hanging
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(processor._extract_citations_unified, sample_text)
                try:
                    # Set a 30-second timeout for the extraction
                    citations = future.result(timeout=30)
                    logger.info(f"Extraction completed. Got {len(citations) if citations else 0} citations")
                except concurrent.futures.TimeoutError:
                    logger.error("Citation extraction timed out after 30 seconds")
                    raise TimeoutError("Citation extraction timed out after 30 seconds")
        except Exception as e:
            logger.error(f"Error during citation extraction: {str(e)}", exc_info=True)
            raise
        
        if not citations:
            logger.warning("No citations were extracted from the text")
            return False
            
        logger.info(f"Extracted {len(citations)} citations")
        
        # Print basic citation info with more details
        for i, citation in enumerate(citations, 1):
            print(f"\n=== Citation {i} ===")
            print(f"Text: {getattr(citation, 'citation', str(citation))}")
            print("\nAttributes:")
            
            # Get all attributes of the citation object
            attrs = {}
            for attr in dir(citation):
                if not attr.startswith('_') and not callable(getattr(citation, attr)):
                    try:
                        value = getattr(citation, attr)
                        # Skip large attributes that might clutter the output
                        if not isinstance(value, (list, dict)) or (isinstance(value, (list, dict)) and len(str(value)) < 100):
                            attrs[attr] = value
                    except Exception as e:
                        attrs[attr] = f"<Error getting attribute: {str(e)}>"
            
            # Print attributes in a readable format
            for key, value in attrs.items():
                print(f"  {key}: {value}")
            
            # Print known important attributes with special formatting
            print("\nImportant Fields:")
            important_fields = [
                'case_name', 'canonical_name', 'extracted_case_name',
                'year', 'extracted_date', 'canonical_date',
                'canonical_url', 'verified', 'is_verified',
                'confidence', 'method', 'source'
            ]
            for field in important_fields:
                value = getattr(citation, field, "<Not Set>")
                print(f"  {field}: {value}")
        
        # Now test clustering and verification
        logger.info("\nTesting clustering and verification...")
        from src.unified_citation_clustering import cluster_citations_unified
        
        # Disable verification for testing to avoid API calls
        clustering_result = cluster_citations_unified(
            citations, 
            sample_text, 
            enable_verification=False  # Disable verification for testing
        )
        
        # Process the clustering result
        if isinstance(clustering_result, dict):
            citations = clustering_result.get('citations', citations)
            clusters = clustering_result.get('clusters', [])
        else:
            clusters = clustering_result if isinstance(clustering_result, list) else []
        
        # Print clustered citations
        logger.info(f"\nFound {len(clusters)} citation clusters")
        for i, cluster in enumerate(clusters, 1):
            print(f"\nCluster {i}:")
            for citation in cluster:
                print(f"  - {getattr(citation, 'citation', str(citation))}")
                print(f"    Case: {getattr(citation, 'canonical_name', 'N/A')} ({getattr(citation, 'canonical_date', 'N/A')})")
                print(f"    URL: {getattr(citation, 'canonical_url', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in test_citation_processing: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    print("Testing citation processor with sample text...")
    success = test_citation_processing()
    sys.exit(0 if success else 1)
