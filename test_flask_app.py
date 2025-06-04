import sys
import os
import logging

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


def test_flask_app():
    """Test the Flask application setup."""
    try:
        logger.info("Testing Flask application setup...")

        # Import the create_app function
        from src.app_final_vue import create_app

        # Create the Flask app
        app = create_app()

        # Test basic app configuration
        assert app is not None, "Failed to create Flask app"
        assert app.config.get("SECRET_KEY") is not None, "SECRET_KEY is not set"

        # Test a simple route
        with app.test_client() as client:
            # Test root route
            response = client.get("/")
            assert response.status_code in [
                200,
                302,
            ], f"Root route failed with status {response.status_code}"

            # Test health check endpoint with the correct URL
            response = client.get("/casestrainer/api/health")
            assert (
                response.status_code == 200
            ), f"Health check failed with status {response.status_code}"

            # Verify the response data
            data = response.get_json()
            assert data.get("status") == "ok", "Health check did not return 'ok' status"
            assert "timestamp" in data, "Health check response is missing timestamp"
            assert (
                data.get("service") == "CaseStrainer API"
            ), "Unexpected service name in health check"

            data = response.get_json()
            assert data.get("status") == "ok", "Health check did not return 'ok' status"

        logger.info("Flask application tests passed!")
        return True

    except Exception as e:
        logger.error(f"Flask application test failed: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    if test_flask_app():
        logger.info("All Flask application tests passed!")
        sys.exit(0)
    else:
        logger.error("Some tests failed. Check the logs above for details.")
        sys.exit(1)
