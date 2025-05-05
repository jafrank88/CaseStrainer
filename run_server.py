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

def run_server():
    """Run the CaseStrainer web application using Waitress."""
    parser = argparse.ArgumentParser(description='Run CaseStrainer web application with Waitress')
    parser.add_argument('--threads', type=int, default=8, help='Number of threads')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--connection-limit', type=int, default=1000, help='Maximum number of connections')
    parser.add_argument('--channel-timeout', type=int, default=120, help='Channel timeout in seconds')
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
    cert_path = os.environ.get('SSL_CERT_PATH', 'D:/dify/docker/nginx/ssl/WolfCertBundle.crt')
    key_path = os.environ.get('SSL_KEY_PATH', 'D:/dify/docker/nginx/ssl/wolf.law.uw.edu.key')
    
    # Enable SSL
    use_ssl = True
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print(f"Using SSL certificate: {cert_path}")
        print(f"Using SSL key: {key_path}")
        use_ssl = True
        
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
            
            # Create SSL adapter with server_side=True to disable client verification
            ssl_adapter = cheroot.ssl.builtin.BuiltinSSLAdapter(cert_path, key_path)
            # Set SSL context to not verify hostname
            ssl_adapter.context.check_hostname = False
            
            # Create server with correct parameters
            server = cheroot.wsgi.Server(
                bind_addr=(args.host, args.port),
                wsgi_app=app,
                server_name='casestrainer',
                numthreads=args.threads,
                request_queue_size=args.connection_limit,
                timeout=args.channel_timeout
            )
            
            # Set SSL adapter
            server.ssl_adapter = ssl_adapter
            
            print(f"Starting CaseStrainer with {args.threads} threads")
            print(f"Server will be available at https://{args.host}:{args.port}")
            
            try:
                server.start()
            except KeyboardInterrupt:
                print("Server stopped.")
                server.stop()
            
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
    
    try:
        # Use a simpler configuration for Waitress
        waitress.serve(
            app,
            host=args.host,
            port=args.port,
            threads=args.threads,
            url_scheme='http'
        )
    except KeyboardInterrupt:
        print("Server stopped.")
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()
