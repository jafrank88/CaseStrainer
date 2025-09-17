"""
Focused test script to debug citation clustering issues.
"""
import logging
import sys
from pprint import pprint

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class SimpleCitation:
    """Simple citation class for testing."""
    def __init__(self, text, start=0, end=0, type_="federal"):
        self.text = text
        self.citation = text
        self.start = start
        self.end = end
        self.type = type_
        self.extracted_case_name = None
        self.extracted_date = None
        self.verification = {}
    
    def __repr__(self):
        return f"SimpleCitation('{self.text}')"

def test_clustering():
    """Test the clustering functionality."""
    try:
        from src.unified_citation_clustering import UnifiedCitationClusterer
        from src.config import get_citation_config
        
        logger.info("=== Starting Clustering Test ===")
        
        # Create test citations
        citations = [
            SimpleCitation("123 F.3d 456"),
            SimpleCitation("456 U.S. 789"),
            SimpleCitation("789 F.2d 123")
        ]
        
        # Get config and enable debug
        config = get_citation_config()
        config['debug_mode'] = True
        config['enable_verification'] = False  # Disable verification for now
        
        # Initialize clusterer
        logger.info("Initializing clusterer...")
        clusterer = UnifiedCitationClusterer(config=config)
        
        # Test direct method call
        logger.info("Testing _detect_parallel_citation_groups...")
        try:
            groups = clusterer._detect_parallel_citation_groups(citations, "Test document")
            logger.info(f"Found {len(groups)} citation groups")
            for i, group in enumerate(groups, 1):
                logger.info(f"Group {i}: {[c.text for c in group]}")
            return True
        except Exception as e:
            logger.error(f"Error in _detect_parallel_citation_groups: {str(e)}", exc_info=True)
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    test_clustering()
