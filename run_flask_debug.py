import os
import sys
import logging
from datetime import datetime

# Set up logging
log_file = "flask_debug.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def log(message, level="info"):
    """Helper function to log messages with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"{timestamp} - {message}"

    # Write to log file
    with open(log_file, "a") as f:
        f.write(log_message + "\n")

    # Also print to console
    print(log_message)

    # Log using appropriate level
    getattr(logger, level.lower())(message)


try:
    log("=" * 50)
    log("Starting Flask debug script...")

    # Add project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    log(f"Project root: {project_root}")
    log(f"Python path: {sys.path}")

    # Import the app
    log("\nImporting create_app from src.app_final_vue...")
    try:
        from src.app_final_vue import create_app

        log("Successfully imported create_app")
    except Exception as e:
        log(f"Error importing create_app: {str(e)}", "error")
        raise

    # Create the app
    log("\nCreating Flask app...")
    try:
        app = create_app()
        log("Flask app created successfully")
        log(f"App name: {app.name}")
        log(f"Instance path: {app.instance_path}")
    except Exception as e:
        log(f"Error creating Flask app: {str(e)}", "error")
        raise

    # Run the app
    log("\nStarting Flask development server...")
    log("Server will be available at: http://0.0.0.0:5000/")
    log("Press Ctrl+C to stop the server")

    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False, threaded=True)

except Exception as e:
    log("\n" + "!" * 50, "error")
    log(f"FATAL ERROR: {type(e).__name__}", "error")
    log(f"Message: {str(e)}", "error")
    log("\nTraceback:", "error")
    log(traceback.format_exc(), "error")

    # Keep the window open
    input("\nPress Enter to exit...")
