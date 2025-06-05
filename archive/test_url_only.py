import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("url_test.log")],
)
logger = logging.getLogger("url_test")

# Base URL for the API
BASE_URL = "http://localhost:5000"

# Test URL
TEST_URL = "https://www.law.cornell.edu/supremecourt/text/347/483"


def test_analyze_endpoint():
    """Test the analyze endpoint with URL input."""
    logger.info("Testing analyze endpoint with URL input...")

    # Prepare the JSON payload
    data = json.dumps({"url": TEST_URL})
    headers = {"Content-Type": "application/json"}

    logger.info(f"Sending URL to analyze endpoint: {TEST_URL}")
    logger.info(f"Request payload: {data}")

    try:
        # Send the request
        response = requests.post(f"{BASE_URL}/api/analyze", data=data, headers=headers)
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"Error response: {response.status_code} - {response.text}")
            return False

        logger.info("URL analysis successful via analyze endpoint")
        logger.info(f"Response: {response.json()}")
        return True
    except Exception as e:
        logger.error(f"Exception during request: {str(e)}")
        return False


def test_direct_url_endpoint():
    """Test the direct_url_analyze endpoint."""
    logger.info("Testing direct_url_analyze endpoint...")

    # Prepare the JSON payload
    data = json.dumps({"url": TEST_URL})
    headers = {"Content-Type": "application/json"}

    logger.info(f"Sending URL to direct_url_analyze endpoint: {TEST_URL}")
    logger.info(f"Request payload: {data}")

    try:
        # Send the request
        response = requests.post(
            f"{BASE_URL}/api/direct_url_analyze", data=data, headers=headers
        )
        logger.info(f"Response status code: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"Error response: {response.status_code} - {response.text}")
            return False

        logger.info("URL analysis successful via direct_url_analyze endpoint")
        logger.info(f"Response: {response.json()}")
        return True
    except Exception as e:
        logger.error(f"Exception during request: {str(e)}")
        return False


def run_tests():
    """Run all tests and report results."""
    logger.info("Starting URL input tests...")

    # Test the analyze endpoint
    analyze_result = test_analyze_endpoint()

    # Test the direct_url_analyze endpoint
    direct_url_result = test_direct_url_endpoint()

    # Report results
    logger.info("\n=== TEST RESULTS SUMMARY ===")
    logger.info(f"analyze_endpoint: {'PASSED' if analyze_result else 'FAILED'}")
    logger.info(f"direct_url_endpoint: {'PASSED' if direct_url_result else 'FAILED'}")

    if not analyze_result or not direct_url_result:
        logger.error("\nSOME TESTS FAILED. Please check the logs for details.")
        return False
    else:
        logger.info("\nALL TESTS PASSED!")
        return True


if __name__ == "__main__":
    run_tests()
