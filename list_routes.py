import sys
import os

# Add the src directory to the path so we can import app_final_vue
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))


def list_routes():
    try:
        from src.app_final import create_app

        print("Creating app instance...")
        app = create_app()

        print("\nRegistered routes:")
        print("-" * 80)

        # Get all routes and sort them
        routes = []
        for rule in app.url_map.iter_rules():
            methods = ",".join(rule.methods - {"OPTIONS", "HEAD"})
            routes.append((str(rule), rule.endpoint, methods))

        # Sort routes by URL
        routes.sort(key=lambda x: x[0])

        # Print routes
        for route, endpoint, methods in routes:
            print(f"{endpoint:50s} {methods:20s} {route}")

        print("\nNote: The API is mounted at /casestrainer/api/")
        print("Example endpoints:")
        print("  GET  /casestrainer/api/version")
        print(
            '  POST /casestrainer/api/analyze -d \'{"text":"Sample text with citation 534 F.3d 1290"}\''
        )

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    list_routes()
