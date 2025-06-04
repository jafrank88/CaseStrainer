import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def test_verify_citation(citation_text, base_url="http://localhost:5000"):
    """
    Test the verify_citation endpoint with a given citation.

    Args:
        citation_text: The citation to verify (e.g., "534 F.3d 1290")
        base_url: Base URL of the API (default: http://localhost:5000)
    """
    try:
        endpoint = f"{base_url}/api/verify_citation"

        logger.info("\n" + "=" * 80)
        logger.info(f"TESTING CITATION VERIFICATION: {citation_text}")
        logger.info(f"Endpoint: {endpoint}")
        logger.info("=" * 80)

        # Prepare the request
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        payload = {"citation_text": citation_text}

        # Make the request
        logger.info("Sending request to verify citation...")
        response = requests.post(endpoint, headers=headers, json=payload)

        # Log the response
        logger.info(f"Status Code: {response.status_code}")

        try:
            response_data = response.json()
            logger.info("Response JSON:")
            print(json.dumps(response_data, indent=2))

            # Check if the citation was verified
            if response_data.get("validation_status") == "verified":
                logger.info("✅ Citation was successfully verified!")
                logger.info(
                    f"Case: {response_data.get('metadata', {}).get('case_name')}"
                )
                logger.info(f"Court: {response_data.get('metadata', {}).get('court')}")
            else:
                logger.warning("❌ Citation was not verified")

        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response")
            logger.error(f"Response text: {response.text}")

    except Exception as e:
        logger.error(f"Error testing citation verification: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())


if __name__ == "__main__":
    # Test with the citation "534 F.3d 1290"
    test_verify_citation("534 F.3d 1290")
