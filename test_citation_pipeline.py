"""
Test script to verify the citation processing pipeline with detailed logging.
"""
import os
import sys
import logging
import json
from typing import List, Dict, Any, Optional

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('citation_pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

class Citation:
    """Simple citation class for testing."""
    def __init__(self, citation: str, text: str, start: int, end: int, type_: str = "federal"):
        self.citation = citation
        self.text = text
        self.start = start
        self.end = end
        self.type = type_
        self.extracted_case_name = None
        self.extracted_date = None
        self.verification = {}
    
    def __str__(self):
        return f"Citation(text='{self.text}', type='{self.type}', case='{self.extracted_case_name}')"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
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

def test_citation_pipeline():
    """Test the citation processing pipeline with detailed logging."""
    try:
        from src.unified_citation_clustering import UnifiedCitationClusterer
        from src.config import get_citation_config
        
        logger.info("=== Starting Citation Pipeline Test ===")
        
        # Create test citations
        citations = [
            Citation("123 F.3d 456", "123 F.3d 456", 0, 12),
            Citation("456 U.S. 789", "456 U.S. 789", 20, 32),
            Citation("789 F.2d 123", "789 F.2d 123", 40, 52)
        ]
        
        logger.info(f"Created {len(citations)} test citations")
        
        # Get configuration
        config = get_citation_config()
        logger.info("Configuration loaded successfully")
        
        # Enable debug mode
        config['debug_mode'] = True
        
        # Initialize clusterer
        logger.info("Initializing UnifiedCitationClusterer...")
        clusterer = UnifiedCitationClusterer(config=config)
        
        # Test clustering
        logger.info("Testing clustering...")
        clusters = clusterer.cluster_citations(citations, "Test document content")
        
        # Log results
        logger.info(f"Clustering completed. Found {len(clusters)} clusters")
        
        for i, cluster in enumerate(clusters, 1):
            logger.info(f"\nCluster {i}:")
            
            # Handle both dict and object access
            if hasattr(cluster, 'citations'):
                cluster_citations = cluster.citations
            elif isinstance(cluster, dict):
                cluster_citations = cluster.get('citations', [])
            else:
                logger.error(f"Unknown cluster type: {type(cluster)}")
                continue
                
            logger.info(f"  Citations in cluster: {len(cluster_citations)}")
            
            for j, citation in enumerate(cluster_citations, 1):
                try:
                    # Convert to dict if it's an object
                    if hasattr(citation, 'to_dict'):
                        citation_data = citation.to_dict()
                    elif hasattr(citation, '__dict__'):
                        citation_data = vars(citation)
                    else:
                        citation_data = dict(citation)
                    
                    logger.info(f"\n  Citation {j}:")
                    logger.info(f"    Text: {citation_data.get('text', 'N/A')}")
                    logger.info(f"    Type: {citation_data.get('type', 'N/A')}")
                    logger.info(f"    Extracted Case: {citation_data.get('extracted_case_name', 'N/A')}")
                    logger.info(f"    Extracted Date: {citation_data.get('extracted_date', 'N/A')}")
                    
                    verification = citation_data.get('verification', {})
                    if verification:
                        logger.info("    Verification:")
                        for key, value in verification.items():
                            logger.info(f"      {key}: {value}")
                    else:
                        logger.warning("    No verification data")
                        
                except Exception as e:
                    logger.error(f"Error processing citation: {str(e)}")
        
        logger.info("\n=== Citation Pipeline Test Completed ===")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    test_citation_pipeline()
