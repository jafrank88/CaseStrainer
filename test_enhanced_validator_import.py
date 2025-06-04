import sys
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)


def main():
    try:
        # Add the project root to the Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)

        logger.info("=" * 50)
        logger.info("TESTING ENHANCED VALIDATOR IMPORTS")
        logger.info("=" * 50)

        # Test importing config
        logger.info("\nTesting import of config...")
        from src.config import get_config_value, configure_logging

        logger.info("✅ Successfully imported from src.config")

        # Test importing citation_processor
        logger.info("\nTesting import of citation_processor...")
        from src.citation_processor import CitationProcessor

        logger.info("✅ Successfully imported from src.citation_processor")

        # Test importing enhanced_validator_production
        logger.info("\nTesting import of enhanced_validator_production...")
        from src.enhanced_validator_production import validate_citations_batch

        logger.info("✅ Successfully imported from src.enhanced_validator_production")

        logger.info("\n✅ All imports successful!")
        return 0

    except ImportError as e:
        logger.error(f"❌ Import error: {str(e)}")
        logger.error(f"Python path: {sys.path}")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
