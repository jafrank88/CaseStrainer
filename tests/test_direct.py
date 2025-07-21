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

# Now import the unified processor instead of deprecated function
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2


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
    """Test citation validation directly using unified processor"""
    debug_print("\n" + "=" * 50)
    debug_print(f"Testing citation: {citation_text}")
    debug_print("=" * 50 + "\n")

    try:
        # Initialize the unified processor
        processor = UnifiedCitationProcessorV2()
        
        # Log the input
        debug_print(f"Test citation: {citation_text}")

        # Call the validation function directly
        debug_print("Calling UnifiedCitationProcessorV2.verify_citation_unified_workflow...")
        result = processor.verify_citation_unified_workflow(citation_text)

        # Print the raw results
        debug_print("\n=== RAW RESULTS ===")
        debug_print(json.dumps(result, indent=2))

        # Print formatted results
        debug_print("\n=== VALIDATION RESULTS ===")
        if result:
            debug_print(f"Status: {result.get('status', 'unknown')}")
            debug_print(f"Citation: {result.get('citation', 'Not found')}")
            debug_print(f"Canonical Name: {result.get('canonical_name', 'N/A')}")
            debug_print(f"Canonical Date: {result.get('canonical_date', 'N/A')}")
            debug_print(f"Verified: {'Yes' if result.get('status') == 'verified' else 'No'}")
        else:
            debug_print("No results returned from validation")

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
