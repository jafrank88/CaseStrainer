from flask import send_from_directory
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)


# Add this function to app_final.py to serve the Vue.js frontend
def add_vue_routes(app):
    """
    Add routes to serve the Vue.js frontend from the Flask application.
    This ensures the Vue.js frontend is accessible through the same URL as the backend.
    """

    # Serve the Vue.js static files
    @app.route("/vue/<path:path>")
    @app.route("/casestrainer/vue/<path:path>")
    def serve_vue_static(path):
        vue_dist_dir = os.path.join(os.path.dirname(__file__), "static", "vue")
        return send_from_directory(vue_dist_dir, path)

    # Serve the Vue.js index.html for all other routes
    @app.route("/vue/")
    @app.route("/casestrainer/vue/")
    def serve_vue_index():
        vue_dist_dir = os.path.join(os.path.dirname(__file__), "static", "vue")
        return send_from_directory(vue_dist_dir, "index.html")

    # Redirect root to Vue.js frontend
    @app.route("/vue")
    @app.route("/casestrainer/vue")
    def redirect_to_vue():
        return serve_vue_index()

    logger.info("Vue.js routes added to Flask application")

    return app
