#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Reverse Proxy for CaseStrainer

This script creates a simple reverse proxy that forwards requests from port 8080 to the CaseStrainer
application running on port 5000. This allows the application to be accessed from a different port
if port 5000 is blocked by firewalls or other network restrictions.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import sys
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('reverse_proxy')

# Constants
TARGET_HOST = "localhost"
TARGET_PORT = 5000
PROXY_PORT = 8080

class ReverseProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request("GET")
    
    def do_POST(self):
        self.proxy_request("POST")
    
    def do_OPTIONS(self):
        self.proxy_request("OPTIONS")
    
    def proxy_request(self, method):
        target_url = f"http://{TARGET_HOST}:{TARGET_PORT}{self.path}"
        logger.info(f"Proxying {method} request to {target_url}")
        
        # Get request headers
        headers = {}
        for header in self.headers:
            headers[header] = self.headers[header]
        
        # Get request body for POST requests
        body = None
        if method == "POST":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
        
        try:
            # Create request
            req = urllib.request.Request(
                url=target_url,
                data=body,
                headers=headers,
                method=method
            )
            
            # Send request to target server
            with urllib.request.urlopen(req) as response:
                # Set response status code
                self.send_response(response.status)
                
                # Set response headers
                for header in response.headers:
                    if header.lower() != 'transfer-encoding':
                        self.send_header(header, response.headers[header])
                
                # Add CORS headers
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                
                self.end_headers()
                
                # Send response body
                self.wfile.write(response.read())
        
        except urllib.error.HTTPError as e:
            logger.error(f"HTTPError: {e.code} - {e.reason}")
            self.send_response(e.code)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f"Error: {e.reason}".encode())
        
        except urllib.error.URLError as e:
            logger.error(f"URLError: {e.reason}")
            self.send_response(502)  # Bad Gateway
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f"Error: {e.reason}".encode())
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.send_response(500)  # Internal Server Error
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())

def run_proxy_server():
    """Run the reverse proxy server."""
    handler = ReverseProxyHandler
    
    with socketserver.TCPServer(("", PROXY_PORT), handler) as httpd:
        logger.info(f"Reverse proxy started on port {PROXY_PORT}")
        logger.info(f"Forwarding requests to {TARGET_HOST}:{TARGET_PORT}")
        logger.info(f"Access the CaseStrainer application at http://localhost:{PROXY_PORT}/")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down reverse proxy...")
            httpd.shutdown()

if __name__ == "__main__":
    # Get command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run a reverse proxy for CaseStrainer')
    parser.add_argument('--target-host', default=TARGET_HOST, help='Target host to forward requests to')
    parser.add_argument('--target-port', type=int, default=TARGET_PORT, help='Target port to forward requests to')
    parser.add_argument('--proxy-port', type=int, default=PROXY_PORT, help='Port to run the proxy server on')
    args = parser.parse_args()
    
    # Update constants with command line arguments
    TARGET_HOST = args.target_host
    TARGET_PORT = args.target_port
    PROXY_PORT = args.proxy_port
    
    # Run the proxy server
    run_proxy_server()
