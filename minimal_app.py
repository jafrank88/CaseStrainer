from flask import Flask
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("minimal_app.log")],
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
