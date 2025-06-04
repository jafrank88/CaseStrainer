import socket
import sys


def test_port(host="0.0.0.0", port=5000):
    print(f"Testing port {port} on {host}")

    # Create a TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)

    try:
        # Try to bind to the port
        print(f"Attempting to bind to {host}:{port}...")
        s.bind((host, port))
        print(f"Successfully bound to {host}:{port}")

        # Start listening
        s.listen(1)
        print(f"Listening on {host}:{port}...")

        # Accept a connection
        print("Waiting for a connection...")
        conn, addr = s.accept()
        print(f"Connection from {addr}")

        # Send a test message
        conn.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHello, World!"
        )

        # Close the connection
        conn.close()

    except socket.error as e:
        print(f"Error: {e}")
        return False
    finally:
        s.close()

    return True


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

    test_port(host, port)
