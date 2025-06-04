import sys
import os
import json
import logging
from pathlib import Path

# Set up basic logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

# Now import the function we want to test
from src.enhanced_validator_production import validate_citations_batch


def main():
    print("=" * 50)
    print("STARTING SIMPLE CITATION VALIDATION TEST")
    print("=" * 50)

    try:
        # Test with a known citation
        test_citation = "534 F.3d 1290"
        print(f"\nTesting citation: {test_citation}")

        # Call the validation function directly
        print("\nCalling validate_citations_batch...")
        results, stats = validate_citations_batch([{"citation_text": test_citation}])

        # Print the results
        print("\n=== RESULTS ===")
        print(json.dumps(results, indent=2))
        print("\n=== STATS ===")
        print(json.dumps(stats, indent=2))

        print("\n✅ Test completed successfully!")
        return 0

    except Exception as e:
        print("\n❌ Test failed!")
        print(f"Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
