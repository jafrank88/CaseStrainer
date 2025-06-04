import sys
import os
import logging
from pathlib import Path

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


def test_imports():
    """Test importing the main application components."""
    try:
        logger.info("Testing imports...")

        # Test importing the main application
        from src.app_final_vue import create_app

        logger.info("Successfully imported create_app from src.app_final_vue")

        # Test creating the app
        app = create_app()
        logger.info("Successfully created Flask app")

        # Test some basic routes
        with app.test_client() as client:
            response = client.get("/")
            logger.info(f"Root route status code: {response.status_code}")

            response = client.get("/casestrainer/api/health")
            logger.info(f"Health check status code: {response.status_code}")

        return True

    except Exception as e:
        logger.error(f"Import test failed: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    if test_imports():
        logger.info("All imports and basic functionality tests passed!")
    else:
        logger.error("Some tests failed. Check the logs above for details.")
        sys.exit(1)
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)


def test_import(module_name, import_path=None):
    """Test importing a module"""
    try:
        logger.info(f"Testing import of {module_name}...")
        if import_path:
            logger.info(f"  Import path: {import_path}")
            try:
                __import__(import_path)
                logger.info(f"[OK] Successfully imported {module_name}")
                return True
            except ImportError as e:
                logger.error(f"[ERROR] Failed to import {module_name}: {e}")
                return False
        else:
            try:
                __import__(module_name)
                logger.info(f"[OK] Successfully imported {module_name}")
                return True
            except ImportError as e:
                logger.error(f"[ERROR] Failed to import {module_name}: {e}")
                return False
    except Exception as e:
        logger.error(f"[ERROR] Error importing {module_name}: {str(e)}")
        return False


def main():
    logger.info("=" * 50)
    logger.info("TESTING IMPORTS")
    logger.info("=" * 50)

    # Add project root to Python path
    project_root = str(Path(__file__).parent.absolute())
    logger.info(f"Project root: {project_root}")
    sys.path.insert(0, project_root)

    # Test basic Python imports
    logger.info("\nTesting basic Python imports...")
    test_import("os")
    test_import("sys")
    test_import("json")

    # Test external dependencies
    logger.info("\nTesting external dependencies...")
    test_import("flask")
    test_import("eyecite")
    test_import("regex")
    test_import("reporters_db")

    # Test local imports
    logger.info("\nTesting local imports...")
    test_import("src.config", "src.config")
    test_import("src.citation_processor", "src.citation_processor")
    test_import(
        "src.enhanced_validator_production", "src.enhanced_validator_production"
    )

    logger.info("\nImport tests completed!")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        sys.exit(1)
