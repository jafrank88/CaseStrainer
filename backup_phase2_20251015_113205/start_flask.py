import os
import sys
import subprocess
import time
import threading
from typing import Callable, Any


class TimeoutError(Exception):
    """Custom exception for timeout errors."""

    pass


def run_with_timeout(func: Callable, timeout: int, *args, **kwargs) -> Any:
    """Run a function with a timeout using threads.

    Args:
        func: The function to run
        timeout: Timeout in seconds
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function

    Raises:
        TimeoutError: If the function doesn't complete within the timeout
    """
    result_container = []
    exception_container = []

    def worker():
        try:
            result_container.append(func(*args, **kwargs))
        except Exception as e:
            exception_container.append(e)

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise TimeoutError(
            f"Function {func.__name__} timed out after {timeout} seconds"
        )
    elif exception_container:
        raise exception_container[0]
    else:
        return result_container[0]


def check_port_in_use(port: int, timeout: int = 5) -> bool:
    """Check if a port is in use."""
    import socket

    def _check():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    try:
        return run_with_timeout(_check, timeout)
    except TimeoutError:
        print(f"Warning: Port check timed out after {timeout} seconds")
        return False


def start_flask_app(timeout: int = 30) -> None:
    """Start the Flask application with a timeout.

    Args:
        timeout: Maximum time to wait for the application to start (in seconds)
    """
    print(f"Starting Flask application with {timeout}s timeout...")

    # Add the current directory and src directory to the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, "src")
    sys.path.insert(0, current_dir)
    sys.path.insert(0, src_dir)

    # Set environment variables
    os.environ["FLASK_APP"] = "src/app_final_vue.py"
    os.environ["FLASK_ENV"] = "development"

    # Check if the port is already in use
    if check_port_in_use(5000):
        print("Port 5000 is already in use. Trying to find the process...")
        try:
            # Find and kill the process using the port
            result = subprocess.run(
                ["netstat", "-ano", "|", "findstr", ":5000"],
                capture_output=True,
                text=True,
                shell=True,
                timeout=10,
            )
            if result.returncode == 0:
                pid = result.stdout.strip().split()[-1]
                print(f"Found process with PID {pid}. Attempting to terminate...")
                subprocess.run(["taskkill", "/F", "/PID", pid], timeout=10)
                time.sleep(2)  # Give it a moment to terminate
        except Exception as e:
            print(f"Error checking/killing process: {e}")

    try:
        # Start the Flask application in a separate process
        cmd = [sys.executable, "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]

        print(f"Running: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=current_dir,
        )

        # Wait for the application to start or timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            if check_port_in_use(5000, timeout=2):
                print("\nFlask application started successfully!")
                print("Access the application at: http://localhost:5000")
                print("Press Ctrl+C to stop the application\n")

                # Stream the output
                try:
                    while True:
                        output = process.stdout.readline()
                        if output == "" and process.poll() is not None:
                            break
                        if output:
                            print(output.strip())
                except KeyboardInterrupt:
                    print("\nStopping Flask application...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        print("Force stopping Flask application...")
                        process.kill()
                finally:
                    return

            # Print a progress indicator
            elapsed = int(time.time() - start_time)
            print(
                f"\rWaiting for Flask to start... {elapsed}s/{timeout}s",
                end="",
                flush=True,
            )
            time.sleep(1)

        # If we get here, the application didn't start in time
        print(f"\nError: Flask application did not start within {timeout} seconds")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    except Exception as e:
        print(f"Error starting Flask application: {e}")
        if "process" in locals():
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
        sys.exit(1)


if __name__ == "__main__":
    try:
        # Start the Flask application with a 30-second timeout
        start_flask_app(timeout=30)
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
