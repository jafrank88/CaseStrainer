"""
Test script to verify citation processor functionality.
This script can be run directly to test the citation processor.
"""

import sys
import os
import logging
import asyncio
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('citation_processor_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

class CitationProcessorTester:
    """Helper class to test citation processor functionality."""
    
    def __init__(self):
        self.processor = None
    
    async def initialize(self):
        """Initialize the citation processor."""
        try:
            from unified_citation_processor_v2 import UnifiedCitationProcessorV2
            self.processor = UnifiedCitationProcessorV2()
            logger.info("Successfully initialized citation processor")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize citation processor: {e}")
            return False
    
    async def test_citation_extraction(self, text: str) -> Dict[str, Any]:
        """Test citation extraction from text."""
        if not self.processor:
            if not await self.initialize():
                return {"error": "Failed to initialize processor"}
        
        try:
            logger.info("Processing test text...")
            result = await self.processor.process_document_citations(text)
            return result
        except Exception as e:
            logger.error(f"Error processing citations: {e}")
            return {"error": str(e)}

def print_results(results: Dict[str, Any]):
    """Print test results in a readable format."""
    if not results:
        print("No results to display")
        return
    
    if "error" in results:
        print(f"\nERROR: {results['error']}")
        return
    
    print("\n" + "="*80)
    print("CITATION PROCESSING RESULTS")
    print("="*80)
    
    # Print citations
    citations = results.get('citations', [])
    print(f"\nFound {len(citations)} citations:")
    
    for i, cite in enumerate(citations, 1):
        print(f"\n[{i}] {cite.get('citation', 'No citation text')}")
        print(f"    Extracted Name: {cite.get('extracted_case_name', 'N/A')}")
        print(f"    Extracted Date: {cite.get('extracted_date', 'N/A')}")
        print(f"    Canonical Name: {cite.get('canonical_name', 'N/A')}")
        print(f"    Canonical Date: {cite.get('canonical_date', 'N/A')}")
        print(f"    Verified: {cite.get('verified', False)}")
    
    # Print clusters
    clusters = results.get('clusters', [])
    print(f"\nFound {len(clusters)} clusters:")
    
    for i, cluster in enumerate(clusters, 1):
        print(f"\nCluster {i}:")
        print(f"  Extracted Name: {cluster.get('extracted_case_name', 'N/A')}")
        print(f"  Extracted Date: {cluster.get('extracted_date', 'N/A')}")
        print(f"  Citations ({len(cluster.get('citations', []))}):")
        
        for j, cite in enumerate(cluster.get('citations', []), 1):
            if isinstance(cite, dict):
                cite_text = cite.get('citation', 'No citation text')
                print(f"    {j}. {cite_text}")
            else:
                print(f"    {j}. {str(cite)[:100]}...")

async def main():
    """Main test function."""
    # Test text with citations
    test_text = """
    In State v. Smith, 123 Wash. 2d 1, 864 P.2d 87 (1993), the court held that...
    See also 536 P.3d 191 (Wash. 2023) and 169 Wn.2d 815, 239 P.3d 354 (2010).
    """
    
    logger.info("Starting citation processor test...")
    tester = CitationProcessorTester()
    
    logger.info("Running citation extraction test...")
    results = await tester.test_citation_extraction(test_text)
    
    # Print results
    print_results(results)
    logger.info("Test completed. Check citation_processor_test.log for details.")

if __name__ == "__main__":
    asyncio.run(main())
