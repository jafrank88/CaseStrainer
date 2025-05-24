import subprocess
import sys
import os
import time
import signal
import psutil
import argparse
from pathlib import Path


def find_available_port(start_port=5000):
    """Find an available port starting from start_port."""
    import socket

    port = start_port
    while port < start_port + 1000:  # Try up to 1000 ports
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            port += 1
    raise RuntimeError("No available ports found")


def start_instance(port, env="development"):
    """Start a single instance of the application."""
    cmd = [
        sys.executable,
        "src/app_final_vue.py",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
        "--env",
        env,
        "--use-cheroot",
    ]

    # Start the process
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Wait for server to start
    time.sleep(2)

    return process


def stop_instance(process):
    """Stop a running instance."""
    if process.poll() is None:  # Process is still running
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def main():
    parser = argparse.ArgumentParser(
        description="Run multiple instances of CaseStrainer"
    )
    parser.add_argument(
        "--instances", type=int, default=3, help="Number of instances to run"
    )
    parser.add_argument(
        "--env",
        choices=["development", "production"],
        default="development",
        help="Environment to run in",
    )
    args = parser.parse_args()

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Start instances
    processes = []
    ports = []

    try:
        for i in range(args.instances):
            port = find_available_port(5000 + (i * 100))
            ports.append(port)

            # Start instance
            process = start_instance(port, args.env)
            processes.append(process)

            print(f"Started instance {i+1} on port {port}")

            # Wait a bit between starts
            time.sleep(1)

        print("\nRunning instances:")
        for i, (process, port) in enumerate(zip(processes, ports)):
            print(f"Instance {i+1}: http://localhost:{port}")

        print("\nPress Ctrl+C to stop all instances")

        # Keep running until interrupted
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping all instances...")
    finally:
        # Stop all instances
        for process in processes:
            stop_instance(process)
        print("All instances stopped")


if __name__ == "__main__":
    main()
