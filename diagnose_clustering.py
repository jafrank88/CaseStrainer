"""
Diagnostic script to check clustering and verification functionality.
"""
import os
import sys
import logging
import json
from typing import Dict, Any, List, Optional

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('diagnose_clustering.log')
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'citation': self.citation,
            'text': self.text,
            'start': self.start,
            'end': self.end,
            'type': self.type
        }

def test_citation_processing():
    """Test the citation processing pipeline."""
    try:
        # Import required modules
        from src.config import get_citation_config
        from src.unified_citation_clustering import UnifiedCitationClusterer
        
        logger.info("=== Starting Citation Processing Diagnostic ===")
        
        # 1. Check configuration
        logger.info("1. Checking configuration...")
        config = get_citation_config()
        logger.info(f"Configuration loaded: {json.dumps(config, indent=2, default=str)}")
        
        # 2. Create test citations
        logger.info("\n2. Creating test citations...")
        test_citations = [
            Citation("123 F.3d 456", "123 F.3d 456", 0, 12),
            Citation("456 U.S. 789", "456 U.S. 789", 20, 32),
            Citation("789 F.2d 123", "789 F.2d 123", 40, 52)
        ]
        logger.info(f"Created {len(test_citations)} test citations")
        
        # 3. Initialize clusterer
        logger.info("\n3. Initializing UnifiedCitationClusterer...")
        clusterer = UnifiedCitationClusterer(config=config)
        
        # 4. Test clustering
        logger.info("\n4. Testing clustering...")
        clusters = clusterer.cluster_citations(test_citations, "Test document content")
        logger.info(f"Clustering completed. Found {len(clusters)} clusters")
        
        # 5. Output results
        logger.info("\n5. Clustering results:")
        for i, cluster in enumerate(clusters, 1):
            logger.info(f"Cluster {i}:")
            if hasattr(cluster, '__dict__'):
                cluster = cluster.__dict__
            
            # Handle both dict and object access
            citations = cluster.get('citations', [])
            logger.info(f"  Citations in cluster: {len(citations)}")
            
            for j, citation in enumerate(citations, 1):
                try:
                    # Handle both dict and object access safely
                    if hasattr(citation, 'text'):
                        # Object access
                        logger.info(f"  Citation {j}:")
                        logger.info(f"    Text: {getattr(citation, 'text', 'N/A')}")
                        logger.info(f"    Type: {getattr(citation, 'type', 'N/A')}")
                        
                        # Check for verification data
                        verification = getattr(citation, 'verification', {})
                    else:
                        # Dictionary access
                        logger.info(f"  Citation {j}:")
                        logger.info(f"    Text: {citation.get('text', 'N/A')}")
                        logger.info(f"    Type: {citation.get('type', 'N/A')}")
                        
                        # Check for verification data
                        verification = citation.get('verification', {})
                    
                    if verification:
                        logger.info("    Verification data found!")
                        # Handle both dict and object access for verification
                        if hasattr(verification, 'get'):
                            # Dictionary-like access
                            logger.info(f"    Status: {verification.get('status', 'N/A')}")
                            result = verification.get('result', {})
                            if result:
                                logger.info(f"    Case name: {result.get('case_name', 'N/A')}")
                                logger.info(f"    Court: {result.get('court', 'N/A')}")
                        else:
                            # Object access
                            logger.info(f"    Status: {getattr(verification, 'status', 'N/A')}")
                            result = getattr(verification, 'result', None)
                            if result:
                                logger.info(f"    Case name: {getattr(result, 'case_name', 'N/A')}")
                                logger.info(f"    Court: {getattr(result, 'court', 'N/A')}")
                    else:
                        logger.warning("    No verification data found!")
                        
                except Exception as e:
                    logger.error(f"    Error processing citation: {str(e)}")
                    logger.error(f"    Citation type: {type(citation)}")
                    logger.error(f"    Citation data: {str(citation)[:200]}...")
        
        logger.info("\n=== Diagnostic completed successfully ===")
        return True
    
    except Exception as e:
        logger.error(f"Diagnostic failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    test_citation_processing()
