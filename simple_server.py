from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket
import os


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


class MyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Hello, World!")


if __name__ == "__main__":
    port = 5000
    local_ip = get_local_ip()

    print(f"Starting server on {local_ip}:{port}")
    print(f"Try accessing: http://{local_ip}:{port}")
    print("Press Ctrl+C to stop")

    try:
        httpd = HTTPServer(("0.0.0.0", port), MyHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")
