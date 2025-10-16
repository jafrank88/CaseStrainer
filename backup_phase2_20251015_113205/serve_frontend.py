#!/usr/bin/env python3
import http.server
import socketserver
import os
from urllib.parse import urlparse

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path.startswith('/casestrainer/'):
            # Remove /casestrainer/ prefix and serve from static directory
            self.path = path.replace('/casestrainer', '', 1)
            os.chdir('static')
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == "__main__":
    PORT = 8080
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print(f"Frontend available at http://localhost:{PORT}/casestrainer/")
        httpd.serve_forever()