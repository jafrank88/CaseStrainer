import sys
import os


def list_routes(app):
    output = []
    for rule in app.url_map.iter_rules():
        methods = ",".join(rule.methods)
        line = "{:50s} {:20s} {}".format(rule.endpoint, methods, rule)
        output.append(line)

    for line in sorted(output):
        print(line)


def create_app():
    # Add the src directory to the path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

    # Import the app factory function
    from app_final_vue import create_app

    # Create the app instance
    app = create_app()
    return app


if __name__ == "__main__":
    print("Creating Flask app...")
    app = create_app()

    print("\nRegistered routes:")
    print("-" * 80)
    list_routes(app)

    print("\nAvailable endpoints:")
    print("  GET  /api/version")
    print("  POST /api/analyze")
    print("  GET  /api/confirmed_with_multitool_data")
    print("  GET  /api/processing_progress")
    print("  POST /api/validate_citations")
