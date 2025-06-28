from flask import Flask
import logging
import os

# Configure logging
# Use project root logs directory
project_root = os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(project_root, "logs")
os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(os.path.join(logs_dir, "minimal_app.log"))],
)

app = Flask(__name__)


@app.route("/")
def hello():
    app.logger.info("Hello endpoint was called")
    return "Hello, World!"


if __name__ == "__main__":
    print("Starting minimal Flask app...")
    print(f"App name: {__name__}")
    print("Starting server on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
