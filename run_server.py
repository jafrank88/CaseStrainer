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
        ssl_adapter.context.check_hostname = False
        ssl_adapter.context.verify_mode = ssl.CERT_NONE  # Disable certificate verification
        
        # Set minimum TLS version to TLS 1.2 for better security
        ssl_adapter.context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Set cipher suite to modern secure ciphers
        ssl_adapter.context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
        
        # Create server - use a different port for each worker to avoid conflicts
        from wsgi import app
        
        # If worker_id > 0, use a different port to avoid conflicts
        worker_port = port + worker_id if worker_id > 0 else port
        
        server = cheroot.wsgi.Server(
            bind_addr=(host, worker_port),
            wsgi_app=app,
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
    
    # Check if Waitress is installed
    try:
        import waitress
    except ImportError:
        print("Waitress is not installed. Installing now...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "waitress"])
            print("Waitress installed successfully.")
            import waitress
        except subprocess.CalledProcessError:
            print("Failed to install Waitress. Please install it manually with 'pip install waitress'.")
            sys.exit(1)
    
    # Import the Flask app
    from wsgi import app
    
    # Check for SSL certificate and key
    cert_path = os.environ.get('SSL_CERT_PATH', 'ssl/cert.pem')
    key_path = os.environ.get('SSL_KEY_PATH', 'ssl/key.pem')
    
    # Enable SSL
    use_ssl = True
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"Using SSL certificate: {cert_path}")
        print(f"Using SSL key: {key_path}")
        use_ssl = True
        
        # Check if we should use multiple worker processes
        if args.workers > 1:
            print(f"Starting {args.workers} worker processes with {args.threads} threads each")
            try:
                import multiprocessing
                
                # Start worker processes
                processes = []
                for i in range(args.workers):
                    p = multiprocessing.Process(
                        target=worker_process,
                        args=(args.host, args.port, args.threads, args.connection_limit, args.channel_timeout, cert_path, key_path, i)
                    )
                    p.daemon = True
                    p.start()
                    processes.append(p)
                
                print(f"Workers started on ports {args.port} to {args.port + args.workers - 1}")
                
                # Wait for all processes to complete
                for p in processes:
                    p.join()
                
                return
            except ImportError:
                print("Multiprocessing not available. Running with a single process.")
        
        # For SSL support, we'll use a separate WSGI server that supports SSL directly
        # Waitress doesn't have built-in SSL support, so we'll use CherryPy's server
        try:
            print("Setting up SSL with CherryPy's WSGI server...")
            
            # Try to import CherryPy
            try:
                import cheroot.wsgi
                import cheroot.ssl.builtin
            except ImportError:
                print("CherryPy/Cheroot not installed. Installing now...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "cheroot"])
                import cheroot.wsgi
                import cheroot.ssl.builtin
                print("CherryPy/Cheroot installed successfully.")
            
            # Create SSL adapter with more robust settings
            ssl_adapter = cheroot.ssl.builtin.BuiltinSSLAdapter(cert_path, key_path)
            
            # Configure SSL context with more robust settings
            ssl_adapter.context.check_hostname = False
            ssl_adapter.context.verify_mode = ssl.CERT_NONE  # Disable certificate verification
            
            # Set minimum TLS version to TLS 1.2 for better security
            ssl_adapter.context.minimum_version = ssl.TLSVersion.TLSv1_2
            
            # Set cipher suite to modern secure ciphers
            ssl_adapter.context.set_ciphers('ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384')
            
            # Create server with correct parameters - explicitly bind to all interfaces
            server = cheroot.wsgi.Server(
                bind_addr=('0.0.0.0', args.port),
                wsgi_app=app,
                server_name='casestrainer',
                numthreads=args.threads,
                request_queue_size=args.connection_limit,
                timeout=args.channel_timeout
            )
            
            # Set maximum request body size
            
            # Set maximum request body size (this is done at the Flask level)
            from wsgi import app
            app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max request size
            print("Maximum request body size set to 100MB")
            
            # Set SSL adapter
            server.ssl_adapter = ssl_adapter
            
            print(f"Starting CaseStrainer with {args.threads} threads")
            print(f"Server will be available at https://{args.host}:{args.port}")
            print("\nIMPORTANT: To analyze PDF files, use the 'Choose File' button in the web interface.")
            print("Do not enter file:/// URLs in the text area, as the server cannot access files on your local machine directly.")
            
            try:
                # Add a custom error handler for SSL errors
                def ssl_error_handler(exc, environ, start_response, traceback=None):
                    status = '400 Bad Request'
                    headers = [('Content-Type', 'text/plain')]
                    start_response(status, headers)
                    return [b'HTTPS is required for this server. Please use a secure connection.']
                
                # Set the error handler
                server.error_handler = ssl_error_handler
                
                # Start the server
                server.start()
            except KeyboardInterrupt:
                print("Server stopped.")
                server.stop()
            except ssl.SSLError as e:
                print(f"SSL Error: {e}")
                print("This is likely due to a client attempting to connect with an incompatible SSL/TLS version.")
                print("The server will continue running.")
                # Restart the server
                server.start()
            
            return
        except Exception as e:
            print(f"Error setting up SSL: {e}")
            print("Falling back to HTTP...")
            use_ssl = False
    else:
        print("Warning: SSL certificate or key not found. Running without SSL.")
        print("For production use with Word add-in, HTTPS is required.")
    
    # If we get here, we're running without SSL
    print(f"Starting CaseStrainer with {args.threads} threads")
    print(f"Server will be available at http://{args.host}:{args.port}")
    
    # Check if we should use multiple worker processes
    if args.workers > 1 and not use_ssl:
        print(f"Starting {args.workers} worker processes with {args.threads} threads each")
        try:
            import multiprocessing
            
            # Start worker processes
            processes = []
            for i in range(args.workers):
                p = multiprocessing.Process(
                    target=http_worker_process,
                    args=(args.host, args.port, args.threads, args.connection_limit, args.channel_timeout, args.timeout, i)
                )
                p.daemon = True
                p.start()
                processes.append(p)
            
            print(f"Workers started on ports {args.port} to {args.port + args.workers - 1}")
            
            # Wait for all processes to complete
            for p in processes:
                p.join()
            
            return
        except ImportError:
            print("Multiprocessing not available. Running with a single process.")
    
    try:
        # Use a simpler configuration for Waitress
        waitress.serve(
            app,
            host=args.host,
            port=args.port,
            threads=args.threads,
            url_scheme='http',
            connection_limit=args.connection_limit,
            channel_timeout=args.channel_timeout,
            cleanup_interval=args.timeout
        )
    except KeyboardInterrupt:
        print("Server stopped.")
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()
