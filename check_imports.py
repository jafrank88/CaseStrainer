import sys
import os
import logging

# Configure logging to file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("import_test.log", mode="w"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def test_import(module_name, import_path=None):
    """Test importing a module."""
    try:
        logger.info(f"Testing import of {module_name}...")
        if import_path:
            logger.info(f"  Import path: {import_path}")
            __import__(import_path)
        else:
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
    # Test core Python modules
    test_import("os")
    test_import("sys")
    test_import("json")

    # Test external dependencies
    test_import("flask")
    test_import("eyecite")
    test_import("regex")
    test_import("reporters_db")

    # Test local imports
    test_import("src.config", "src.config")
    test_import("src.citation_utils", "src.citation_utils")

    try:
        # Try to import the main application
        from src.app_final_vue import create_app

        logger.info("[OK] Successfully imported create_app from src.app_final_vue")

        # Create the Flask app
        app = create_app()
        logger.info("[OK] Successfully created Flask app")

        # Test basic configuration
        assert app is not None, "Failed to create Flask app"
        assert app.config.get("SECRET_KEY") is not None, "SECRET_KEY is not set"

        logger.info("[OK] All tests passed!")
        return 0

    except Exception as e:
        logger.error(f"[ERROR] Error testing Flask app: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
