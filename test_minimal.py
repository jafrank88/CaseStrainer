"""
Enhanced test script to verify the citation processing pipeline with verification.
"""
import os
import sys
import logging
import json
from typing import List, Dict, Any

# Configure logging with UTF-8 encoding
class UTF8StreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            stream.write(msg.replace('\u2705', '[OK]').replace('\u274c', '[X]') + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        UTF8StreamHandler(),
        logging.FileHandler('citation_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class Citation:
    """Simple citation class for testing."""
    def __init__(self, citation, text, start, end, type_="federal"):
        self.citation = citation
        self.text = text
        self.start = start
        self.end = end
        self.type = type_
        self.extracted_case_name = None
        self.extracted_date = None
        self.verification = {}
    
    def __str__(self):
        return (f"Citation(text='{self.text}', type='{self.type}', "
                f"case='{self.extracted_case_name}', date='{self.extracted_date}')")

def test_citation_processing():
    """Test the complete citation processing pipeline."""
    try:
        # Import required modules
        from src.unified_citation_clustering import UnifiedCitationClusterer
        from src.config import get_citation_config
        
        logger.info("=== Starting Citation Processing Test ===")
        
        # 1. Create test citations
        citations = [
            Citation("123 F.3d 456", "123 F.3d 456", 0, 12),
            Citation("456 U.S. 789", "456 U.S. 789", 20, 32),
            Citation("789 F.2d 123", "789 F.2d 123", 40, 52)
        ]
        logger.info(f"Created {len(citations)} test citations")
        
        # 2. Get configuration
        config = get_citation_config()
        config.update({
            'debug_mode': True,
            'enable_verification': True,
            'clustering_options': {
                'enable_parallel_detection': True,
                'enable_case_relationship_detection': True,
                'enable_metadata_propagation': True
            },
            'verification_options': {
                'enable_courtlistener': True,
                'enable_fallback_sources': True,
                'enable_confidence_scoring': True,
                'min_confidence_threshold': 0.7
            }
        })
        
        # 3. Initialize clusterer
        logger.info("Initializing UnifiedCitationClusterer...")
        clusterer = UnifiedCitationClusterer(config=config)
        
        # 4. Run clustering with verification
        logger.info("Running citation clustering...")
        clusters = clusterer.cluster_citations(
            citations, 
            "Test document content",
            enable_verification=True
        )
        
        # 5. Process and log results
        logger.info(f"\n=== Clustering Results ({len(clusters)} clusters) ===")
        
        for i, cluster in enumerate(clusters, 1):
            logger.info(f"\nCluster {i}:")
            
            # Handle both object and dict access
            if hasattr(cluster, 'citations'):
                cluster_citations = cluster.citations
            elif isinstance(cluster, dict):
                cluster_citations = cluster.get('citations', [])
            else:
                cluster_citations = []
            
            logger.info(f"  Citations in cluster: {len(cluster_citations)}")
            
            for j, citation in enumerate(cluster_citations, 1):
                try:
                    # Convert to dict for consistent access
                    if hasattr(citation, 'to_dict'):
                        cite_data = citation.to_dict()
                    elif hasattr(citation, '__dict__'):
                        cite_data = vars(citation)
                    else:
                        cite_data = dict(citation)
                    
                    logger.info(f"\n  Citation {j}:")
                    logger.info(f"    Text: {cite_data.get('text', 'N/A')}")
                    logger.info(f"    Type: {cite_data.get('type', 'N/A')}")
                    logger.info(f"    Extracted Case: {cite_data.get('extracted_case_name', 'N/A')}")
                    logger.info(f"    Extracted Date: {cite_data.get('extracted_date', 'N/A')}")
                    
                    # Check verification data
                    verification = cite_data.get('verification', {})
                    if verification:
                        logger.info("    Verification:")
                        if isinstance(verification, dict):
                            for key, value in verification.items():
                                if key == 'result' and value:
                                    logger.info("      Result:")
                                    if hasattr(value, 'items'):
                                        for k, v in value.items():
                                            logger.info(f"        {k}: {v}")
                                    else:
                                        logger.info(f"        {value}")
                                else:
                                    logger.info(f"      {key}: {value}")
                        else:
                            logger.info(f"      {verification}")
                    else:
                        logger.warning("    No verification data")
                        
                except Exception as e:
                    logger.error(f"Error processing citation: {str(e)}")
        
        logger.info("\n=== Test Completed Successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    test_citation_processing()
