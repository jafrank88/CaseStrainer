import socket
import sys


def check_port(host="localhost", port=5000, timeout=5):
    """Check if a port is open and accepting connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error checking port {port}: {e}")
        return False


def main():
    print("Testing connection to CaseStrainer API...")

    if not check_port():
        print("\n❌ Could not connect to the API server on port 5000.")
        print("Please make sure the server is running with:")
        print("  python src/app_final_vue.py --debug --env development")
        sys.exit(1)

    print("\n✅ Successfully connected to the API server on port 5000!")
    print("You can now access the API at: http://localhost:5000/casestrainer/api/")
    print("\nTry these example endpoints:")
    print("  GET  /casestrainer/api/version")
    print(
        '  POST /casestrainer/api/analyze -d \'{"text":"Sample text with citation 534 F.3d 1290"}\''
    )


if __name__ == "__main__":
    main()
