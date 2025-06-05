import sys
import logging
from pathlib import Path

# Force immediate output
import functools

print = functools.partial(print, flush=True)

# Set up logging to both console and file
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),  # Log to stderr for immediate output
        logging.FileHandler("test.log", mode="w"),  # Log to file for debugging
    ],
)

# Add project root to Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

# Import the function we want to test
print("Importing validate_citations_batch...")
from src.enhanced_validator_production import validate_citations_batch


def main():
    print("\n" + "=" * 50)
    print("MINIMAL CITATION VALIDATION TEST")
    print("=" * 50 + "\n")

    try:
        # Test citation
        citation = "534 F.3d 1290"
        print(f"Testing citation: {citation}")

        # Call the function
        print("\nCalling validate_citations_batch...")
        results, stats = validate_citations_batch([{"citation_text": citation}])

        # Print results
        print("\n=== VALIDATION RESULTS ===")
        print(f"Results: {results}")
        print(f"Stats: {stats}")

        if results and len(results) > 0:
            result = results[0]
            print(f"\nCitation: {result.get('citation_text')}")
            print(f"Status: {result.get('validation_status')}")
            print(f"Case Name: {result.get('metadata', {}).get('case_name', 'N/A')}")

        print("\n✅ Test completed!")
        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
