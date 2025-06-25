import os
import sys
import json
import logging
import traceback
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

# Set up logging - temporarily set to WARNING to reduce output
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("citation_test")


def load_config():
    """Load configuration from config.json"""
    try:
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config.json: {e}")
        return {}


def test_citation_verification(citation_text):
    """Test citation verification for a given citation."""
    try:
        # Import the necessary functions
        from citation_utils import extract_citations_from_text, verify_citation

        logger.info(f"Testing citation: {citation_text}")

        # Step 1: Extract citation using eyecite
        logger.info("Extracting citations from text...")
        extracted = extract_citations_from_text(citation_text, logger=logger)

        if not extracted:
            logger.warning("No citations found in the text")
            return {"error": "No citations found in the text"}

        logger.info(f"Extracted {len(extracted)} citations")

        # Step 2: Verify each citation
        results = []
        for citation in extracted:
            try:
                # Handle different citation object structures
                if isinstance(citation, dict):
                    citation_text = citation.get(
                        "citation_text", citation.get("citation", str(citation))
                    )
                    context = citation.get("context", "")
                else:
                    citation_text = str(citation)
                    context = ""

                logger.info(f"Verifying citation: {citation_text}")

                # Verify the citation
                verification = verify_citation(
                    citation_text, context=context, logger=logger
                )

                results.append(
                    {
                        "citation_text": citation_text,
                        "context": context,
                        "verification": verification,
                    }
                )

            except Exception as e:
                logger.error(f"Error processing citation {citation}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                results.append({"citation_text": str(citation), "error": str(e)})

        return results

    except Exception as e:
        logger.error(f"Error in citation verification: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"error": str(e), "traceback": traceback.format_exc()}


if __name__ == "__main__":
    # Load configuration
    config = load_config()

    # Get API key from config
    api_key = config.get("COURTLISTENER_API_KEY") or config.get("courtlistener_api_key")
    if not api_key:
        logger.error("No CourtListener API key found in config.json")
        sys.exit(1)

    # Set the API key in environment
    os.environ["COURTLISTENER_API_KEY"] = api_key

    # Test with the specified citation
    citation = "534 F.3d 1290"
    print(f"Testing citation: {citation}")

    try:
        # Run the test
        results = test_citation_verification(citation)

        # Print the results in a more readable format
        print("\n" + "=" * 80)
        print(f"VERIFICATION RESULTS FOR CITATION: {citation}")
        print("=" * 80)

        if isinstance(results, dict) and "error" in results:
            print(f"\nError: {results['error']}")
            if "traceback" in results:
                print("\nTraceback:")
                print(results["traceback"])
            sys.exit(1)

        if not results:
            print("\nNo verification results returned.")
            sys.exit(0)

        for i, result in enumerate(results, 1):
            print(f"\n{'='*40}")
            print(f"RESULT {i}")
            print(f"{'='*40}")

            if "error" in result:
                print(f"Error: {result['error']}")
                continue

            print(f"Citation: {result.get('citation_text', 'N/A')}")

            verification = result.get("verification", {})
            if not verification:
                print("No verification data available")
                continue

            print("\nVerification Details:")
            print(f"- Status: {verification.get('status', 'N/A')}")
            print(f"- Verified: {verification.get('verified', False)}")

            if "case_name" in verification:
                print(f"- Case Name: {verification['case_name']}")

            if "citation" in verification:
                print(f"- Citation: {verification['citation']}")

            if "docket_number" in verification:
                print(f"- Docket Number: {verification['docket_number']}")

            if "decision_date" in verification:
                print(f"- Decision Date: {verification['decision_date']}")

            if "court" in verification:
                print(f"- Court: {verification['court']}")

            if "url" in verification:
                print(f"- URL: {verification['url']}")

            if "error" in verification:
                print(f"\nError: {verification['error']}")

    except Exception as e:
        print("\n" + "!" * 80)
        print(f"ERROR DURING VERIFICATION: {str(e)}")
        print("!" * 80)
        logger.error(f"Error during citation verification: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
