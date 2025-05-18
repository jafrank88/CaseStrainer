import os
import sys

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

# Import the Vue API blueprint
from vue_api import vue_api

app = Flask(__name__, static_folder='static/vue')
app.config.from_object(Config)

# Add URL prefix handling
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)

# Register Vue.js API blueprint
app.register_blueprint(vue_api, url_prefix='/api')

# Import and register the enhanced validator blueprint
try:
    from enhanced_validator_production import enhanced_validator_bp, register_enhanced_validator
    app.register_blueprint(enhanced_validator_bp, url_prefix='/api/enhanced')
    register_enhanced_validator()
    print("Enhanced Validator registered successfully")
except ImportError as e:
    print(f"Warning: Could not import enhanced validator: {e}")
    print("The application will run with basic validation only.")
except Exception as e:
    print(f"Error registering enhanced validator: {e}")
    print("The application will run with basic validation only.")

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_vue(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Use host='0.0.0.0' to allow Docker Nginx to access
    app.run(host='0.0.0.0', port=5000, debug=False)
