import os
import sys

# Add the src directory to the Python path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Set environment variables
os.environ["FLASK_APP"] = "app_final_vue.py"
os.environ["FLASK_DEBUG"] = "1"

# Import and run the Flask app
from app_final_vue import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
