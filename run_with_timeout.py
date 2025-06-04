import subprocess
import sys
import time
import threading
import os


def run_with_timeout(command, timeout_seconds=60):
    """Run a command with a timeout."""
    print(f"Running command: {' '.join(command)}")
    print(f"Timeout set to {timeout_seconds} seconds")

    # Start the process
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    print(f"Process started with PID: {process.pid}")

    # Set up a timer to kill the process if it times out
    def kill_process():
        try:
            process.terminate()
            process.wait(timeout=5)  # Give it a moment to terminate gracefully
        except subprocess.TimeoutExpired:
            process.kill()  # Force kill if it doesn't terminate

    timer = threading.Timer(timeout_seconds, kill_process)
    timer.daemon = True
    timer.start()

    # Stream the output
    while True:
        output = process.stdout.readline()
        if output == "" and process.poll() is not None:
            break
        if output:
            print(output.strip())

    # Clean up the timer
    timer.cancel()

    # Get any remaining output
    stdout, stderr = process.communicate()
    if stdout:
        print(stdout.strip())
    if stderr:
        print(stderr.strip(), file=sys.stderr)

    return process.returncode


if __name__ == "__main__":
    # Command to run the application with detailed logging
    command = [
        sys.executable,
        "-u",  # Unbuffered output
        "-m",
        "src.app_final_vue",
        "--host",
        "0.0.0.0",
        "--port",
        "5000",
        "--debug",
    ]

    # Set a 60-second timeout
    print("Starting application with detailed logging...")
    return_code = run_with_timeout(command, timeout_seconds=60)

    if return_code != 0:
        print(f"Application failed with return code {return_code}", file=sys.stderr)
        sys.exit(return_code)
