from flask import Flask
import logging
import os
import sys

# Configure logging
# Use project root logs directory
project_root = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(project_root, "logs")
os.makedirs(logs_dir, exist_ok=True)

log_file = os.path.join(logs_dir, "minimal_app_5001.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="w"),
        logging.StreamHandler(sys.stdout),
    ],
)

app = Flask(__name__)


@app.route("/")
def hello():
    app.logger.info("Hello endpoint was called")
    return "Hello, World on port 5001!"


if __name__ == "__main__":
    print("Starting minimal Flask app on port 5001...")
    print(f"App name: {__name__}")
    print("Starting server on http://127.0.0.1:5001")
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
