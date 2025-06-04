import sys
import os
import json
import logging
from pathlib import Path

# Set up logging to a file
log_file = "direct_test_output.txt"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=log_file,
    filemode="w",
)

logger = logging.getLogger(__name__)


def log(message):
    """Log a message to both console and file"""
    print(message)  # This will show in the console
    logger.info(message)  # This will be written to the file


def test_import(module_name):
    """Test importing a module"""
    try:
        log(f"Testing import of {module_name}...")
        __import__(module_name)
        log(f"✅ Successfully imported {module_name}")
        return True
    except ImportError as e:
        log(f"❌ Failed to import {module_name}: {str(e)}")
        return False
    except Exception as e:
        log(f"❌ Error importing {module_name}: {str(e)}")
        return False


def main():
    log("=" * 50)
    log("DIRECT FILE TEST - CHECKING IMPORTS")
    log("=" * 50 + "\n")

    # Add project root to Python path
    project_root = str(Path(__file__).parent.absolute())
    log(f"Project root: {project_root}")
    sys.path.insert(0, project_root)

    # Test basic Python imports
    log("\nTesting basic Python imports...")
    test_import("os")
    test_import("sys")
    test_import("json")

    # Test external dependencies
    log("\nTesting external dependencies...")
    test_import("flask")
    test_import("eyecite")
    test_import("regex")
    test_import("reporters_db")

    # Test local imports
    log("\nTesting local imports...")
    test_import("src.config")

    # Try to import the specific function we need
    try:
        log("\nTrying to import get_config_value from src.config...")
        from src.config import get_config_value

        log("✅ Successfully imported get_config_value from src.config")
    except Exception as e:
        log(f"❌ Failed to import get_config_value: {str(e)}")

    log("\nTest completed!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"❌ Unhandled exception: {str(e)}")
        import traceback

        log(traceback.format_exc())
        sys.exit(1)
