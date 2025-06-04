import sys
import os
import logging
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def test_citation_validation(citation_text):
    try:
        # Import the enhanced validator
        from src.enhanced_validator_production import (
            validate_citations_batch,
            citation_processor,
        )

        logger.info("\n" + "=" * 80)
        logger.info(f"DIRECT CITATION VALIDATION: {citation_text}")
        logger.info("=" * 80)

        # Validate the citation
        logger.info("Validating citation...")
        results, stats = validate_citations_batch([{"citation_text": citation_text}])

        # Print the results
        logger.info("\nVALIDATION RESULTS:")
        logger.info(f"Status: {results[0].get('validation_status', 'UNKNOWN')}")
        logger.info(
            f"Case Name: {results[0].get('metadata', {}).get('case_name', 'Not found')}"
        )
        logger.info(
            f"Court: {results[0].get('metadata', {}).get('court', 'Not found')}"
        )
        logger.info(
            f"Date Filed: {results[0].get('metadata', {}).get('date_filed', 'Not found')}"
        )

        # Print the full response in a pretty format
        import json

        logger.info("\nFULL RESPONSE:")
        print(json.dumps(results[0], indent=2))

        return True

    except Exception as e:
        logger.error(f"Error validating citation: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    # Test with the citation "534 F.3d 1290"
    test_citation_validation("534 F.3d 1290")
