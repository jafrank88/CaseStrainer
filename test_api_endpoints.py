import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000/casestrainer/api"


def test_version():
    """Test the version endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/version")
        response.raise_for_status()
        version_info = response.json()
        logger.info(f"Version: {json.dumps(version_info, indent=2)}")
        return True
    except Exception as e:
        logger.error(f"Error testing version endpoint: {str(e)}")
        return False


def test_verify_citation(citation_text):
    """Test the verify_citation endpoint."""
    try:
        response = requests.post(
            f"{BASE_URL}/verify_citation", json={"citation_text": citation_text}
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"Verification result for '{citation_text}':")
        logger.info(json.dumps(result, indent=2))
        return True
    except Exception as e:
        logger.error(f"Error verifying citation: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return False


def test_analyze_text(text):
    """Test the analyze endpoint with text input."""
    try:
        response = requests.post(f"{BASE_URL}/analyze", json={"text": text})
        response.raise_for_status()
        result = response.json()
        logger.info(f"Analysis result for text input:")
        logger.info(f"Status: {result.get('status')}")
        logger.info(f"Analysis ID: {result.get('analysis_id')}")
        return result.get("analysis_id")
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return None


def test_analysis_status(analysis_id):
    """Check the status of an analysis."""
    try:
        response = requests.get(f"{BASE_URL}/status/{analysis_id}")
        response.raise_for_status()
        status = response.json()
        logger.info(f"Status for analysis {analysis_id}:")
        logger.info(json.dumps(status, indent=2))
        return status
    except Exception as e:
        logger.error(f"Error checking analysis status: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return None


if __name__ == "__main__":
    logger.info("Testing API endpoints...")

    # Test version endpoint
    logger.info("\n=== Testing version endpoint ===")
    test_version()

    # Test citation verification
    logger.info("\n=== Testing citation verification ===")
    test_verify_citation("534 F.3d 1290")  # Test with a known good citation

    # Test text analysis
    logger.info("\n=== Testing text analysis ===")
    test_text = """
    The court in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) held that
    the plaintiff's claims were without merit. This decision was later
    cited with approval in Doe v. Roe, 534 F.3d 1290 (10th Cir. 2008).
    """
    analysis_id = test_analyze_text(test_text)

    # Check analysis status if we got an analysis ID
    if analysis_id:
        logger.info("\n=== Testing analysis status ===")
        test_analysis_status(analysis_id)
