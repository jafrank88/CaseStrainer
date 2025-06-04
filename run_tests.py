import unittest
import logging
import sys
from test_api import TestCitationAPI


def main():
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    logger = logging.getLogger(__name__)

    try:
        # Create a test suite
        test_suite = unittest.TestLoader().loadTestsFromTestCase(TestCitationAPI)

        # Run the test suite
        test_runner = unittest.TextTestRunner(verbosity=2)
        test_result = test_runner.run(test_suite)

        # Exit with appropriate status code
        sys.exit(not test_result.wasSuccessful())

    except Exception as e:
        logger.error(f"Error running tests: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
