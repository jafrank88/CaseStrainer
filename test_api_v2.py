import requests
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000/casestrainer/api"


def test_analyze_text():
    """Test the analyze endpoint with text input."""
    try:
        test_text = """
        The court in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) held that
        the plaintiff's claims were without merit. This decision was later
        cited with approval in Doe v. Roe, 534 F.3d 1290 (10th Cir. 2008).
        """

        response = requests.post(f"{BASE_URL}/analyze", json={"text": test_text})
        response.raise_for_status()
        result = response.json()
        logger.info("Analysis result for text input:")
        logger.info(f"Status: {result.get('status')}")
        logger.info(f"Analysis ID: {result.get('analysis_id')}")
        return result.get("analysis_id")
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return None


def test_verify_citation():
    """Test the verify_citation endpoint."""
    try:
        response = requests.post(
            f"{BASE_URL}/verify_citation", json={"citation_text": "534 F.3d 1290"}
        )
        response.raise_for_status()
        result = response.json()
        logger.info("Verification result for '534 F.3d 1290':")
        logger.info(json.dumps(result, indent=2))
        return True
    except Exception as e:
        logger.error(f"Error verifying citation: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return False


def test_unconfirmed_citations():
    """Test the unconfirmed citations endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/unconfirmed-citations-data")
        response.raise_for_status()
        result = response.json()
        logger.info("Unconfirmed citations:")
        logger.info(f"Found {len(result.get('citations', []))} unconfirmed citations")
        return True
    except Exception as e:
        logger.error(f"Error getting unconfirmed citations: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response: {e.response.text}")
        return False


if __name__ == "__main__":
    logger.info("Testing API endpoints...")

    # Test text analysis
    logger.info("\n=== Testing text analysis ===")
    analysis_id = test_analyze_text()

    # Test citation verification
    logger.info("\n=== Testing citation verification ===")
    test_verify_citation()

    # Test unconfirmed citations
    logger.info("\n=== Testing unconfirmed citations ===")
    test_unconfirmed_citations()
