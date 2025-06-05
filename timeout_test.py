import sys
import signal
import time
import json
import logging
from pathlib import Path

# Set up logging to both console and file
log_file = "timeout_test.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(log_file, mode="w"),
    ],
)

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Test timed out after 30 seconds")


def run_with_timeout(func, timeout_seconds=30):
    """Run a function with a timeout"""
    # Set the signal handler
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        return func()
    finally:
        # Disable the alarm
        signal.alarm(0)


def test_citation_validation():
    """Test the citation validation function"""
    logger.info("=" * 50)
    logger.info("TIMEOUT CITATION VALIDATION TEST")
    logger.info("=" * 50)

    try:
        # Add project root to Python path
        project_root = str(Path(__file__).parent.absolute())
        sys.path.insert(0, project_root)

        # Import the function we want to test
        logger.info("Importing validate_citations_batch...")
        from src.enhanced_validator_production import validate_citations_batch

        # Test citation
        citation = "534 F.3d 1290"
        logger.info(f"Testing citation: {citation}")

        # Call the function with a timeout
        logger.info("Calling validate_citations_batch...")

        def run_validation():
            return validate_citations_batch([{"citation_text": citation}])

        logger.info("Starting validation with 30-second timeout...")
        start_time = time.time()
        results, stats = run_with_timeout(run_validation, 30)
        elapsed = time.time() - start_time

        # Print results
        logger.info(f"Validation completed in {elapsed:.2f} seconds")
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

        logger.info("\n✅ Test completed successfully!")
        return 0

    except TimeoutError as te:
        logger.error(f"❌ {str(te)}")
        return 1
    except ImportError as ie:
        logger.error(f"❌ Import error: {str(ie)}")
        return 1
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(test_citation_validation())
    except Exception as e:
        logger.critical(f"❌ Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)
