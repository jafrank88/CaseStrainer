from flask import Flask, jsonify, request
import time
import sys

app = Flask(__name__)

# Counter to simulate crashes
error_counter = 0

# Enable logging to file
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("flask_test.log"), logging.StreamHandler(sys.stdout)],
)


@app.route("/")
def hello():
    global error_counter
    error_counter += 1

    client_ip = request.remote_addr
    app.logger.info(f"Request #{error_counter} from {client_ip}")

    # Simulate a crash after 3 requests
    if error_counter > 3 and error_counter < 6:
        # Return error for requests 4 and 5
        app.logger.warning(f"Simulating error for request #{error_counter}")
        return f"Simulated error (request #{error_counter})", 500
    elif error_counter >= 6:
        # Crash the server on 6th request
        app.logger.error(f"Crashing server on request #{error_counter}")
        import os

        os._exit(1)

    return (
        f"Hello! This is request #{error_counter}. Server will simulate errors soon..."
    )


@app.route("/health")
def health():
    app.logger.info("Health check endpoint called")
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": time.time(),
                "requests_served": error_counter,
            }
        ),
        200,
    )


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Starting test Flask server on http://localhost:5000/")
    print("The server will:")
    print("1. Work normally for the first 3 requests")
    print("2. Return 500 errors for requests 4-5")
    print("3. Crash on the 6th request")
    print("=" * 60 + "\n")

    # Log startup information
    import socket
    import os

    try:
        # Get local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        app.logger.info(f"Hostname: {hostname}")
        app.logger.info(f"Local IP: {local_ip}")
        app.logger.info(f"Process ID: {os.getpid()}")

        # Try to bind to the port to check for port conflicts
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.bind(("0.0.0.0", 5000))
                app.logger.info("Port 5000 is available")
            except OSError as e:
                app.logger.error(f"Port 5000 is not available: {e}")
                raise

        # Start the Flask development server
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

    except Exception as e:
        app.logger.error(f"Server error: {str(e)}")
        app.logger.error("Stack trace:", exc_info=True)

        # Keep the process alive for a while to allow reading logs
        print("\nServer failed to start. Waiting 60 seconds before exiting...")
        import time

        time.sleep(60)

        raise
