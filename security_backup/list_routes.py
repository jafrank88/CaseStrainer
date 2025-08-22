import logging

# Setup logging
logger = logging.getLogger(__name__)

from src.app_final_vue import app

if __name__ == "__main__":
    logger.info("Available routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"{rule.endpoint}: {rule.methods} -> {rule}")
