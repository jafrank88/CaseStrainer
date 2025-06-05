import subprocess
import time
import requests
import json
import sys
import os
import logging
from datetime import datetime
from src.enhanced_multi_source_verifier import EnhancedMultiSourceVerifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("test_verifier.log"), logging.StreamHandler()],
)
logger = logging.getLogger("TestVerifier")

# Configuration
SERVER_SCRIPT = "start_casestrainer.bat"
TEST_CITATION = "534 F.3d 1290"
SERVER_URL = "http://localhost:5000"
API_ENDPOINT = f"{SERVER_URL}/api/analyze"
MAX_WAIT_TIME = 30  # seconds to wait for server to start
LOG_FILE = "test_log.txt"


def log_message(message):
    """Log message to console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def start_server():
    """Start the CaseStrainer server"""
    log_message("Starting CaseStrainer server...")
    try:
        # Start the server in a new process
        server_process = subprocess.Popen(
            [SERVER_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            bufsize=1,
            universal_newlines=True,
        )
        return server_process
    except Exception as e:
        log_message(f"Error starting server: {e}")
        return None


def wait_for_server(timeout=MAX_WAIT_TIME):
    """Wait for the server to become available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{SERVER_URL}/api/health", timeout=2)
            if response.status_code == 200:
                log_message("Server is up and running!")
                return True
        except requests.RequestException:
            time.sleep(1)
            continue
    log_message("Timed out waiting for server to start")
    return False


def test_direct_verification():
    """Test the EnhancedMultiSourceVerifier directly"""
    logger.info("Testing EnhancedMultiSourceVerifier directly...")

    try:
        # Initialize the verifier
        verifier = EnhancedMultiSourceVerifier()

        # Test a known citation
        test_citation = "534 F.3d 1290"
        logger.info(f"Testing citation: {test_citation}")

        # Verify the citation
        result = verifier.verify_citation(test_citation)

        # Log the result
        logger.info(f"Verification result: {json.dumps(result, indent=2, default=str)}")

        # Check if the result is a dictionary
        if not isinstance(result, dict):
            logger.error(f"Expected dict but got {type(result).__name__}")
            return False

        # Check required fields
        required_fields = ["verified", "citation", "source"]
        for field in required_fields:
            if field not in result:
                logger.error(f"Missing required field: {field}")
                return False

        logger.info(
            f"Citation verification successful: {result.get('verified', False)}"
        )
        return True

    except Exception as e:
        logger.error(f"Error in direct verification test: {e}", exc_info=True)
        return False


def test_api_verification():
    """Test the citation verification through the API endpoint"""
    logger.info("Testing citation verification API...")

    try:
        test_citation = "534 F.3d 1290"
        test_data = {"citation": test_citation}

        logger.info(f"Sending request to {API_ENDPOINT}")
        response = requests.post(
            API_ENDPOINT,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        logger.info(f"Response status: {response.status_code}")

        try:
            result = response.json()
            logger.info(f"API Response: {json.dumps(result, indent=2, default=str)}")

            # Check if the response has the expected structure
            if not isinstance(result, dict):
                logger.error(f"Expected dict response, got {type(result).__name__}")
                return False

            if "citations" in result and isinstance(result["citations"], list):
                for citation in result["citations"]:
                    if (
                        isinstance(citation, dict)
                        and citation.get("citation") == test_citation
                    ):
                        logger.info("Found matching citation in API response")
                        return True

            logger.warning("Test citation not found in API response")
            return False

        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return False


def main():
    """Main function to run the tests"""
    # Clear the log file
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    logger.info("Starting CaseStrainer test suite...")
    server_process = None

    try:
        # Run direct verification test (doesn't need server)
        logger.info("\n=== Running Direct Verification Test ===")
        direct_result = test_direct_verification()
        logger.info(
            f"Direct verification test {'PASSED' if direct_result else 'FAILED'}"
        )

        # Start the server for API tests
        logger.info("\n=== Starting Server for API Tests ===")
        server_process = start_server()
        if not server_process:
            logger.error("Failed to start server. Skipping API tests.")
            return 1 if not direct_result else 0

        try:
            # Wait for server to start
            logger.info("Waiting for server to start...")
            if not wait_for_server():
                logger.error("Server did not start in time. Exiting.")
                return 1

            # Run API test
            logger.info("\n=== Running API Verification Test ===")
            api_result = test_api_verification()
            logger.info(f"API verification test {'PASSED' if api_result else 'FAILED'}")

            # Final results
            logger.info("\n=== Test Results ===")
            logger.info(
                f"Direct Verification: {'PASSED' if direct_result else 'FAILED'}"
            )
            logger.info(f"API Verification: {'PASSED' if api_result else 'FAILED'}")

            return 0 if (direct_result and api_result) else 1

        finally:
            # Clean up server process
            if server_process:
                logger.info("Stopping server...")
                try:
                    server_process.terminate()
                    server_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(
                        "Server did not terminate gracefully, forcing kill..."
                    )
                    server_process.kill()
                logger.info("Server stopped")

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
