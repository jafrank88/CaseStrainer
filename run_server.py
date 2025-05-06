#!/usr/bin/env python3
"""
Script to run the CaseStrainer web application using Waitress.
This allows multiple users to use the site simultaneously.
"""

import os
import sys
import subprocess
import argparse
import ssl

# Worker process function for multiprocessing
def worker_process(host, port, threads, connection_limit, channel_timeout, cert_path, key_path, worker_id=0):
    try:
        # Import CherryPy for SSL support
        import cheroot.wsgi
        import cheroot.ssl.builtin
        
        # Create SSL adapter with more robust settings
        ssl_adapter = cheroot.ssl.builtin.BuiltinSSLAdapter(cert_path, key_path)
        
        # Configure SSL context with more robust settings
        ssl_adapter.context.check_hostname = True  # Enable hostname checking
        ssl_adapter.context.verify_mode = ssl.CERT_REQUIRED  # Require certificate verification
        
        # Set minimum TLS version to TLS 1.2 for better security
        ssl_adapter.context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Set cipher suite to modern secure ciphers
        ssl_adapter.context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
        
        # Add security headers middleware
        def add_security_headers(environ, start_response):
            def custom_start_response(status, headers, exc_info=None):
                # Add security headers
                headers.extend([
                    ('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload'),
                    ('X-Content-Type-Options', 'nosniff'),
                    ('X-Frame-Options', 'DENY'),
                    ('X-XSS-Protection', '1; mode=block'),
                    ('Content-Security-Policy', "default-src 'self' https://wolf.law.uw.edu; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:;"),
                    ('Referrer-Policy', 'strict-origin-when-cross-origin'),
                    ('Permissions-Policy', 'geolocation=(), microphone=(), camera=()'),
                    ('Access-Control-Allow-Origin', 'https://wolf.law.uw.edu'),
                    ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                ])
                return start_response(status, headers, exc_info)
            
            return app(environ, custom_start_response)
        
        # Create server - use a different port for each worker to avoid conflicts
        from wsgi import app
        
        # If worker_id > 0, use a different port to avoid conflicts
        worker_port = port + worker_id if worker_id > 0 else port
        
        server = cheroot.wsgi.Server(
            bind_addr=(host, worker_port),
            wsgi_app=add_security_headers,
            server_name=f'casestrainer-worker-{worker_id}',
            numthreads=threads,
            request_queue_size=connection_limit,
            timeout=channel_timeout
        )
        
        # Set SSL adapter
        server.ssl_adapter = ssl_adapter
        
        # Add a custom error handler for SSL errors
        def ssl_error_handler(exc, environ, start_response, traceback=None):
            status = '400 Bad Request'
            headers = [('Content-Type', 'text/plain')]
            start_response(status, headers)
            return [b'HTTPS is required for this server. Please use a secure connection.']
        
        # Set the error handler
        server.error_handler = ssl_error_handler
        
        # Start server with error handling
        try:
            server.start()
        except ssl.SSLError as e:
            print(f"Worker {worker_id} SSL Error: {e}")
            print("This is likely due to a client attempting to connect with an incompatible SSL/TLS version.")
            print("The worker will continue running.")
            # Restart the server
            server.start()
    except Exception as e:
        print(f"Worker process error: {e}")

# HTTP worker process
def http_worker_process(host, port, threads, connection_limit, channel_timeout, cleanup_interval, worker_id=0):
    try:
        # Use Waitress for HTTP - use a different port for each worker to avoid conflicts
        import waitress
        from wsgi import app
        
        # If worker_id > 0, use a different port to avoid conflicts
        worker_port = port + worker_id if worker_id > 0 else port
        
        waitress.serve(
            app,
            host=host,
            port=worker_port,
            threads=threads,
            url_scheme='http',
            connection_limit=connection_limit,
            channel_timeout=channel_timeout,
            cleanup_interval=cleanup_interval
        )
    except Exception as e:
        print(f"Worker process error: {e}")

def run_server():
    """Run the CaseStrainer web application using Waitress."""
    parser = argparse.ArgumentParser(description='Run CaseStrainer web application with Waitress')
    parser.add_argument('--threads', type=int, default=8, help='Number of threads')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes (requires multiprocessing)')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--connection-limit', type=int, default=2000, help='Maximum number of connections')
    parser.add_argument('--channel-timeout', type=int, default=300, help='Channel timeout in seconds')
    parser.add_argument('--timeout', type=int, default=300, help='Worker timeout in seconds')
    args = parser.parse_args()
    
    print(f"Starting server with configuration:")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Threads: {args.threads}")
    print(f"Workers: {args.workers}")
    
    # Use Waitress for HTTP
    try:
        import waitress
        from wsgi import app
        
        print(f"Starting CaseStrainer with {args.threads} threads")
        print(f"Server will be available at http://{args.host}:{args.port}")
        print("Note: SSL is handled by Nginx")
        
        # Configure Waitress with basic settings
        waitress.serve(
            app,
            host=args.host,
            port=args.port,
            threads=args.threads,
            url_scheme='https',  # Set to https since we're behind SSL
            connection_limit=args.connection_limit,
            channel_timeout=args.channel_timeout,
            trusted_proxy='127.0.0.1',  # Trust the local Nginx proxy
            trusted_proxy_headers={'x-forwarded-for', 'x-forwarded-proto', 'x-forwarded-host'}
        )
    except KeyboardInterrupt:
        print("Server stopped.")
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()
