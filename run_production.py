import os
import sys
from waitress import serve
from src.app_final_vue import app
import logging
import socket
from datetime import datetime


# --- URL Prefix Middleware ---
class PrefixMiddleware:
    def __init__(self, app, prefix):
        self.app = app
        self.prefix = prefix.rstrip("/")

    def __call__(self, environ, start_response):
        if self.prefix and environ["PATH_INFO"].startswith(self.prefix):
            environ["SCRIPT_NAME"] = self.prefix
            environ["PATH_INFO"] = environ["PATH_INFO"][len(self.prefix) :] or "/"
            return self.app(environ, start_response)
        elif not self.prefix:
            return self.app(environ, start_response)
        else:
            from werkzeug.wrappers import Response

            return Response("Not Found", status=404)(environ, start_response)


# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Create a log file with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"casestrainer_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def get_server_info():
    """Get server information for logging."""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return {"hostname": hostname, "ip_address": ip_address}
    except Exception as e:
        logger.error(f"Error getting server info: {e}")
        return {"hostname": "unknown", "ip_address": "unknown"}


def main():
    # Set environment variables
    os.environ["FLASK_ENV"] = "production"

    # Get configuration from environment or use defaults
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    threads = int(os.environ.get("THREADS", 10))

    # Get server information
    server_info = get_server_info()

    # Log startup information
    logger.info("=" * 50)
    logger.info("Starting CaseStrainer in production mode")
    logger.info(f"Server: {server_info['hostname']} ({server_info['ip_address']})")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Threads: {threads}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 50)

    # URL prefix support
    url_prefix = os.environ.get("URL_PREFIX", "/casestrainer")
    if url_prefix and url_prefix != "/":
        logger.info(f"Using URL prefix: {url_prefix}")
        wsgi_app = PrefixMiddleware(app, url_prefix)
    else:
        logger.info("No URL prefix set. Serving at root.")
        wsgi_app = app

    try:
        serve(wsgi_app, host=host, port=port, threads=threads)
    except OSError as e:
        logger.error(f"Failed to start server: {e}")
        if "Address already in use" in str(e):
            logger.error(
                f"Port {port} is already in use. Please free the port and try again."
            )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
