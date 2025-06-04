from flask import Flask
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Force stdout
        logging.FileHandler("minimal_5000.log"),
    ],
)

app = Flask(__name__)


@app.route("/")
def hello():
    app.logger.info("Root endpoint was called")
    return "Hello, World on port 5000!"


@app.route("/test")
def test():
    app.logger.info("Test endpoint was called")
    return "Test endpoint is working!"


if __name__ == "__main__":
    print("=" * 50)
    print("Starting minimal Flask app on port 5000...")
    print(f"Python executable: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    print("=" * 50)

    try:
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=True,
            use_reloader=False,  # Disable reloader to avoid double output
            threaded=True,
        )
    except Exception as e:
        print(f"Failed to start server: {str(e)}")
        raise
