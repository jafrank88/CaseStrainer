import logging
from src.app_final_vue import app

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    print("Starting CaseStrainer server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
