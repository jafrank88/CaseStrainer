#!/usr/bin/env python
"""
Direct runner for CaseStrainer application
This script directly imports and runs the Flask application from app_final_vue.py
"""
import os
import sys
import socket
import subprocess
import time


def check_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) != 0


def kill_process_on_port(port):
    """Kill any process using the specified port"""
    try:
        if os.name == "nt":  # Windows
            output = subprocess.check_output(
                f"netstat -ano | findstr :{port}", shell=True
            ).decode()
            if output:
                for line in output.splitlines():
                    if "LISTENING" in line:
                        pid = line.split()[-1]
                        subprocess.call(f"taskkill /F /PID {pid}", shell=True)
                        print(f"Killed process with PID {pid} using port {port}")
                        return True
        return False
    except subprocess.CalledProcessError:
        return False


def main():
    """Run the CaseStrainer application directly"""
    print("===================================================")
    print("CaseStrainer Direct Runner")
    print("===================================================")

    # Set environment variables
    os.environ["HOST"] = "0.0.0.0"
    os.environ["PORT"] = "5000"
    os.environ["USE_CHEROOT"] = "True"

    # Check if port 5000 is available
    port = 5000
    print(f"Checking if port {port} is available...")
    if not check_port_available(port):
        print(f"Port {port} is in use. Attempting to kill the process...")
        if kill_process_on_port(port):
            print(f"Process using port {port} has been killed.")
            time.sleep(1)  # Give time for the port to be released
        else:
            print(
                f"Could not kill process using port {port}. Please close it manually."
            )
            return 1
    else:
        print(f"Port {port} is available.")

    # Get the path to app_final_vue.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app_final_vue_simple.py")

    if not os.path.exists(app_path):
        print(f"Error: {app_path} not found.")
        app_path = os.path.join(script_dir, "app_final_vue.py")
        if not os.path.exists(app_path):
            print(f"Error: {app_path} not found.")
            return 1

    print(f"Starting CaseStrainer from: {app_path}")
    print("External access will be available at: https://wolf.law.uw.edu/casestrainer/")
    print("Local access will be available at: http://127.0.0.1:5000")

    # Import the Flask application directly
    sys.path.insert(0, script_dir)

    # Try to import and run the Flask application
    try:
        # Change working directory to the script directory
        os.chdir(script_dir)

        # Import the Flask application
        if "app_final_vue_simple.py" in app_path:
            from app_final_vue_simple import app
        else:
            from app_final_vue import app

        # Run the Flask application
        app.run(host="0.0.0.0", port=port)
    except ImportError as e:
        print(f"Error importing Flask application: {e}")
        return 1
    except Exception as e:
        print(f"Error running Flask application: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
