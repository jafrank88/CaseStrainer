"""
Test script to verify synchronous citation processing.
"""
import os
import sys
import time
import logging
import json
from typing import List, Dict, Any, Optional

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # More verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sync_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Disable some noisy loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)

class Citation:
    """Simple citation class for testing."""
    def __init__(self, citation, text=None, start=0, end=0, type_="federal"):
        self.citation = citation
        self.text = text or citation
        self.start = start
        self.end = end
        self.type = type_
        self.extracted_case_name = None
        self.extracted_date = None
        self.verification = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert citation to dictionary format."""
        return {
            'citation': self.citation,
            'text': self.text,
            'start': self.start,
            'end': self.end,
            'type': self.type,
            'extracted_case_name': self.extracted_case_name,
            'extracted_date': self.extracted_date,
            'verification': self.verification
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Citation':
        """Create Citation from dictionary."""
        citation = cls(
            citation=data.get('citation', ''),
            text=data.get('text', ''),
            start=data.get('start', 0),
            end=data.get('end', 0),
            type_=data.get('type', 'federal')
        )
        citation.extracted_case_name = data.get('extracted_case_name')
        citation.extracted_date = data.get('extracted_date')
        citation.verification = data.get('verification', {})
        return citation

    def __repr__(self):
        return f"Citation('{self.citation}')"

def test_sync_processing():
    """Test synchronous citation processing with detailed diagnostics."""
    try:
        from src.unified_citation_clustering import cluster_citations_unified, UnifiedCitationClusterer
        from src.config import get_citation_config
        
        logger.info("=== Starting Synchronous Processing Test ===")
        
        # Get default configuration
        config = get_citation_config()
        
        # Log configuration
        logger.info("Configuration:")
        for key, value in config.items():
            if isinstance(value, dict):
                logger.info(f"  {key}:")
                for k, v in value.items():
                    logger.info(f"    {k}: {v}")
            else:
                logger.info(f"  {key}: {value}")
        
        # Create test citations with different formats
        test_cases = [
            {"name": "Standard US Supreme Court", "citations": ["505 U.S. 1003"]},
            {"name": "Federal Reporter", "citations": ["123 F.3d 456"]},
            {"name": "Federal Reporter 2nd", "citations": ["789 F.2d 123"]},
            {"name": "Parallel Citations", "citations": ["100 S. Ct. 1000", "100 S.Ct. 1000"]}
        ]
        
        all_citations = []
        for case in test_cases:
            for citation_text in case['citations']:
                all_citations.append(Citation(citation_text, type_="federal"))
        
        # Convert to list of dictionaries for processing
        citations_data = [cit.to_dict() for cit in all_citations]
        
        # Log input data
        logger.info("\nInput citations:")
        for i, cit in enumerate(citations_data, 1):
            logger.info(f"  {i}. {cit['citation']} (type: {cit.get('type', 'unknown')})")
        
        # Test 1: Direct cluster_citations_unified function
        logger.info("\n=== Testing cluster_citations_unified ===")
        start_time = time.time()
        clusters = cluster_citations_unified(
            citations=citations_data,
            original_text="Test document content for citation processing",
            enable_verification=True
        )
        end_time = time.time()
        
        # Log results
        logger.info(f"\nSynchronous processing completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Found {len(clusters)} clusters")
        
        # Save detailed results to file
        with open('clustering_results.json', 'w') as f:
            json.dump(clusters, f, indent=2)
        
        # Log cluster details
        for i, cluster in enumerate(clusters, 1):
            logger.info(f"\nCluster {i}:")
            cluster_citations = cluster.get('citations', [])
            logger.info(f"  Citations in cluster: {len(cluster_citations)}")
            
            for j, cit_data in enumerate(cluster_citations, 1):
                citation = Citation.from_dict(cit_data)
                logger.info(f"  Citation {j}: {citation.citation}")
                logger.info(f"    Type: {citation.type}")
                
                # Log verification results if available
                if citation.verification:
                    status = citation.verification.get('status', 'N/A')
                    logger.info(f"    Verification: {status}")
                    if status == 'success':
                        logger.info(f"    Case name: {citation.verification.get('case_name', 'N/A')}")
                        logger.info(f"    Court: {citation.verification.get('court', 'N/A')}")
                        logger.info(f"    Decision date: {citation.verification.get('decision_date', 'N/A')}")
                else:
                    logger.info("    No verification data")
        
        # Test 2: UnifiedCitationClusterer class
        logger.info("\n=== Testing UnifiedCitationClusterer class ===")
        clusterer = UnifiedCitationClusterer(config=config)
        start_time = time.time()
        clusters_class = clusterer.cluster_citations(
            citations=citations_data,
            original_text="Test document content for citation processing"
        )
        end_time = time.time()
        
        logger.info(f"\nClass-based processing completed in {end_time - start_time:.2f} seconds")
        logger.info(f"Found {len(clusters_class)} clusters")
        
        logger.info("\n=== Synchronous Test Completed ===")
        return True
        
    except Exception as e:
        logger.error(f"Synchronous test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # Run synchronous test
    test_sync_processing()
    
    logger.info("\nTest completed. Check sync_test.log for detailed results.")
    logger.info("Clustering results have been saved to clustering_results.json")
