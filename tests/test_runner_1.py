# test_runner.py
import subprocess
import time
import sys


def run_test_cycle():
    print("=" * 50)
    print("Starting Test Cycle")
    print("=" * 50)

    # Start the server
    print("\nStarting server...")
    server_process = subprocess.Popen(
        ["start_casestrainer.bat"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    )

    try:
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(10)  # Give it time to start

        # Run the test
        print("\nRunning citation verification test...")
        result = subprocess.run(
            ["python", "test_citation_verification.py"], capture_output=True, text=True
        )

        # Print test output
        print("\nTest Output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

        print("\nTest completed with return code:", result.returncode)
        return result.returncode == 0

    finally:
        # Stop the server
        print("\nStopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("Server stopped")


def main():
    cycle = 1
    while True:
        print(f"\n{'='*20} CYCLE {cycle} {'='*20}")
        success = run_test_cycle()

        if not success:
            print("\nTest failed! Waiting for next cycle...")
        else:
            print("\nTest passed! Waiting for next cycle...")

        time.sleep(2)  # Wait before next cycle
        cycle += 1


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest runner stopped by user")
        sys.exit(0)
