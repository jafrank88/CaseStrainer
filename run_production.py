import os
import sys
from waitress import serve
from src.app_final_vue import app
import logging
import socket
from datetime import datetime

# Configure logging
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)

# Create a log file with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(log_dir, f'casestrainer_{timestamp}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_server_info():
    """Get server information for logging."""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return {
            'hostname': hostname,
            'ip_address': ip_address
        }
    except Exception as e:
        logger.error(f"Error getting server info: {e}")
        return {
            'hostname': 'unknown',
            'ip_address': 'unknown'
        }

def main():
    # Set environment variables
    os.environ['FLASK_ENV'] = 'production'
    
    # Get configuration from environment or use defaults
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    threads = int(os.environ.get('THREADS', 10))
    
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
    
    try:
        # Run the application with waitress
        serve(app, host=host, port=port, threads=threads)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 