import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))


def load_config():
    """Load configuration from config.json"""
    try:
        config_path = Path(__file__).parent / "config.json"
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return {}


def test_citation():
    """Test citation verification for a single citation"""
    # Load config and get API key
    config = load_config()
    api_key = config.get("COURTLISTENER_API_KEY") or config.get("courtlistener_api_key")

    if not api_key:
        print("Error: No CourtListener API key found in config.json")
        return

    # Set the API key in environment
    import os

    os.environ["COURTLISTENER_API_KEY"] = api_key

    # Import the verification function
    from citation_verification import verify_citation

    # Test citation
    citation = "534 F.3d 1290"
    print(f"Testing citation: {citation}")

    try:
        # Verify the citation
        result = verify_citation(citation)

        # Print the results
        print("\nVerification Results:")
        print("=" * 40)
        print(f"Citation: {citation}")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"Verified: {result.get('verified', False)}")

        if "case_name" in result:
            print(f"Case Name: {result['case_name']}")
        if "citation" in result:
            print(f"Citation: {result['citation']}")
        if "docket_number" in result:
            print(f"Docket Number: {result['docket_number']}")
        if "decision_date" in result:
            print(f"Decision Date: {result['decision_date']}")
        if "court" in result:
            print(f"Court: {result['court']}")
        if "url" in result:
            print(f"URL: {result['url']}")
        if "error" in result:
            print(f"Error: {result['error']}")

    except Exception as e:
        print(f"\nError during verification: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_citation()
