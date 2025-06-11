import sys
import os
import logging
import json
import traceback
from pathlib import Path

# Force immediate output
import functools

print = functools.partial(print, flush=True)

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

# Now import the function we want to test
from src.enhanced_validator_production import validate_citations_batch


def setup_logging():
    """Set up detailed logging configuration"""
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create console handler and set level to debug
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)

    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Add handler to logger
    logger.addHandler(ch)

    # Also log to a file for debugging
    fh = logging.FileHandler("test_direct.log", mode="w")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Log environment information
    logger.info("=" * 50)
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Python Path: {sys.path}")
    logger.info("=" * 50)

    # Log environment variables that might affect the test
    env_vars = ["COURTLISTENER_API_KEY", "FLASK_APP", "FLASK_ENV", "PYTHONPATH"]
    logger.info("Environment Variables:")
    for var in env_vars:
        logger.info(f"  {var}: {os.environ.get(var, 'Not set')}")
    logger.info("=" * 50)


def debug_print(*args, **kwargs):
    """Print to console immediately"""
    print(*args, **{"file": sys.stderr, "flush": True, **kwargs})


def test_citation_validation(citation_text):
    """Test citation validation directly"""
    debug_print("\n" + "=" * 50)
    debug_print(f"Testing citation: {citation_text}")
    debug_print("=" * 50 + "\n")

    try:
        # Log the input
        test_data = [{"citation_text": citation_text}]
        debug_print(f"Test data: {json.dumps(test_data, indent=2)}")

        # Call the validation function directly
        debug_print("Calling validate_citations_batch...")
        results, stats = validate_citations_batch(test_data)

        # Print the raw results
        debug_print("\n=== RAW RESULTS ===")
        debug_print(json.dumps(results, indent=2))
        debug_print("\n=== STATS ===")
        debug_print(json.dumps(stats, indent=2))

        # Print formatted results
        debug_print("\n=== VALIDATION RESULTS ===")
        if results and len(results) > 0:
            result = results[0]
            debug_print(f"Status: {result.get('validation_status', 'unknown')}")
            debug_print(
                f"Case Name: {result.get('metadata', {}).get('case_name', 'Not found')}"
            )
            debug_print(
                f"Validation Method: {result.get('metadata', {}).get('validation_method', 'N/A')}"
            )
            debug_print(
                f"Verified: {'Yes' if result.get('validation_status') == 'verified' else 'No'}"
            )
        else:
            debug_print("No results returned from validation")

        debug_print("\n=== STATISTICS ===")
        debug_print(f"Verified: {stats.get('verified', 0)}")
        debug_print(f"Not Found: {stats.get('not_found', 0)}")
        debug_print(f"Errors: {stats.get('errors', 0)}")

        return True

    except Exception as e:
        debug_print(f"Error during validation: {str(e)}")
        debug_print(traceback.format_exc())
        return False


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    debug_print("=" * 50)
    debug_print("STARTING CITATION VALIDATION TEST")
    debug_print("=" * 50)

    try:
        # Test with a known citation
        test_citation = "534 F.3d 1290"  # Test with a known citation
        debug_print(f"\nStarting test with citation: {test_citation}")

        success = test_citation_validation(test_citation)

        if success:
            debug_print("\n✅ Test completed successfully!")
        else:
            debug_print("\n❌ Test failed!")
            sys.exit(1)

    except Exception as e:
        debug_print("\n!!! UNHANDLED EXCEPTION !!!")
        debug_print(str(e))
        debug_print(traceback.format_exc())
        sys.exit(1)
