import sys
import json
import logging
from pathlib import Path

# Set up logging to both console and file
log_file = "direct_test.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),  # Log to stderr for immediate output
        logging.FileHandler(log_file, mode="w"),  # Log to file for debugging
    ],
)

logger = logging.getLogger(__name__)

# Add project root to Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)


def main():
    logger.info("=" * 50)
    logger.info("DIRECT CITATION VALIDATION TEST")
    logger.info("=" * 50 + "\n")

    try:
        # Import the function we want to test
        logger.info("Importing validate_citations_batch...")
        from src.enhanced_validator_production import validate_citations_batch

        # Test citation
        citation = "534 F.3d 1290"
        logger.info(f"Testing citation: {citation}")

        # Call the function
        logger.info("Calling validate_citations_batch...")
        results, stats = validate_citations_batch([{"citation_text": citation}])

        # Print results
        logger.info("\n=== VALIDATION RESULTS ===")
        logger.info(f"Results: {json.dumps(results, indent=2) if results else 'None'}")
        logger.info(f"Stats: {json.dumps(stats, indent=2) if stats else 'None'}")

        if results and len(results) > 0:
            result = results[0]
            logger.info(f"\nCitation: {result.get('citation_text')}")
            logger.info(f"Status: {result.get('validation_status')}")
            logger.info(
                f"Case Name: {result.get('metadata', {}).get('case_name', 'N/A')}"
            )

        logger.info("\n✅ Test completed!")
        return 0

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)
