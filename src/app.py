# DEPRECATED: Use app_final_vue.py as the single source of truth for the CaseStrainer Flask backend.
# All future development and deployment should reference app_final_vue.py only.

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import json
import logging
import datetime
import traceback
from flask import Flask, send_from_directory, request, jsonify, session, redirect
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS

# Import blueprints and modules
from enhanced_validator_production import (
    enhanced_validator_bp as enhanced_validator_production_bp,
    register_enhanced_validator,
)
from citation_api import citation_api

# Import API blueprint if exists
try:
    from vue_api import api_blueprint
except ImportError:
    api_blueprint = None

UPLOAD_FOLDER = "uploads"
DATABASE_FILE = "citations.db"
ALLOWED_EXTENSIONS = {"txt", "pdf", "docx", "doc"}

# Helper: load config
try:
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "config.json"
    )
    with open(config_path, "r") as f:
        config = json.load(f)
        DEFAULT_API_KEY = config.get("COURTLISTENER_API_KEY", "") or config.get(
            "courtlistener_api_key", ""
        )
        SECRET_KEY = config.get("SECRET_KEY", "")
except Exception as e:
    DEFAULT_API_KEY = os.environ.get("COURTLISTENER_API_KEY", "")
    SECRET_KEY = os.environ.get("SECRET_KEY", "")


# App factory
def create_app():
    app = Flask(__name__, static_folder=None)
    app.config["SECRET_KEY"] = SECRET_KEY or "devkey"
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600 * 24
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["SESSION_FILE_DIR"] = os.path.join(
        os.path.dirname(__file__), "..", "casestrainer_sessions"
    )
    app.config["SESSION_COOKIE_PATH"] = "/casestrainer/"
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    CORS(app)
    Session(app)

    # Register blueprints
    app.register_blueprint(
        enhanced_validator_production_bp, url_prefix="/casestrainer/enhanced-validator"
    )
    app.register_blueprint(citation_api, url_prefix="/casestrainer/api")
    if api_blueprint:
        app.register_blueprint(api_blueprint, url_prefix="/casestrainer/api")
    try:
        register_enhanced_validator(app)
    except Exception as e:
        print(f"Enhanced validator registration failed: {e}")

    # --- Vue.js Frontend Static Serving ---
    @app.route("/casestrainer/")
    def serve_vue_index():
        # Redirect the default landing page to the enhanced validator
        return redirect("/casestrainer/enhanced-validator", code=302)

    @app.route("/casestrainer/<path:path>")
    def serve_vue_assets(path):
        vue_dist_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "casestrainer-vue", "dist")
        )
        file_path = os.path.join(vue_dist_dir, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            response = send_from_directory(vue_dist_dir, path)
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0, post-check=0, pre-check=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "-1"
            response.headers["Last-Modified"] = (
                f"{datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}"
            )
            return response
        else:
            # If not a static file, serve the Vue index.html (SPA shell)
            return send_from_directory(vue_dist_dir, "index.html")

    # Error handlers
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run CaseStrainer Flask App")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=False)
