import os
from dotenv import load_dotenv
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("COURTLISTENER_API_KEY")

if not api_key:
    logger.error("ERROR: COURTLISTENER_API_KEY environment variable is not set")
    print("\nPlease create a .env file in the project root with the following content:")
    print("COURTLISTENER_API_KEY=your_api_key_here\n")
    exit(1)
else:
    logger.info("✓ COURTLISTENER_API_KEY is set")
    logger.info(f"Key length: {len(api_key)} characters")
    logger.info(f"Key starts with: {api_key[:5]}...")
    logger.info("\nAPI key configuration is working correctly!")
    print(
        "\nTo test the actual API call, you can run the enhanced_validator_production.py script."
    )
    print(
        "Or you can run: python -c \"from src.enhanced_validator_production import check_courtlistener_api; print(check_courtlistener_api('410 U.S. 113'))\""
    )
