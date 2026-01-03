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
            response = client.get("/casestrainer/")
            logger.info(f"Root route status code: {response.status_code}")
            assert response.status_code == 200

            response = client.get("/casestrainer/api/health")
            logger.info(f"Health check status code: {response.status_code}")
            assert response.status_code in [200, 207]  # Accept both healthy (200) and degraded (207)

    except Exception as e:
        logger.error(f"Import test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    if test_imports():
        logger.info("All imports and basic functionality tests passed!")
    else:
        logger.error("Some tests failed. Check the logs above for details.")
        sys.exit(1)
