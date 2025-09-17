"""
Test script to verify that clustering and verification are enabled by default in the configuration.
"""
import os
import sys
import logging

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_config():
    """Test that clustering and verification are enabled by default in the config."""
    from src.config import get_citation_config
    
    # Get default configuration
    config = get_citation_config()
    
    # Log the configuration for debugging
    logger.info("Citation configuration:")
    for key, value in config.items():
        if key in ('clustering_options', 'verification_options'):
            logger.info(f"  {key}:")
            for k, v in value.items():
                logger.info(f"    {k} = {v}")
        else:
            logger.info(f"  {key} = {value}")
    
    # Verify default settings
    assert config.get('enable_clustering', False), "Clustering should be enabled by default"
    assert config.get('enable_verification', False), "Verification should be enabled by default"
    
    # Check clustering options
    clustering_options = config.get('clustering_options', {})
    assert clustering_options.get('enable_parallel_detection', False), "Parallel detection should be enabled by default"
    
    # Check verification options
    verification_options = config.get('verification_options', {})
    assert verification_options.get('enable_courtlistener', False), "CourtListener verification should be enabled by default"
    
    logger.info("All configuration tests passed!")

if __name__ == "__main__":
    test_config()
