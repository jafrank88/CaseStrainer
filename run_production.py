#!/usr/bin/env python
"""
Production deployment script for CaseStrainer
Uses Cheroot as a production-ready WSGI server
"""
import os
import sys
import subprocess
import traceback

def main():
    """Run the CaseStrainer application with Cheroot in production mode."""
    print("Starting CaseStrainer in production mode with Cheroot...")
    
    # Ensure Cheroot is installed
    try:
        import cheroot
        print("Cheroot is already installed.")
    except ImportError:
        print("Cheroot not installed. Installing now...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cheroot"])
        print("Cheroot installed successfully.")
    
    # Set environment variables
    os.environ['USE_CHEROOT'] = 'True'
    os.environ['FLASK_ENV'] = 'production'
    os.environ['DEBUG'] = 'False'
    
    # Get configuration from command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run CaseStrainer in production mode')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to (default: 8000)')
    parser.add_argument('--unix-socket', help='Unix socket path (for Nginx, e.g., /tmp/casestrainer.sock)')
    args = parser.parse_args()
    
    # Set host and port environment variables
    if args.unix_socket:
        os.environ['UNIX_SOCKET'] = args.unix_socket
        print(f"Server will start on Unix socket: {args.unix_socket}")
    else:
        os.environ['HOST'] = args.host
        os.environ['PORT'] = str(args.port)
        print(f"Server will start on http://{args.host}:{args.port}")
    
    # Run the application directly instead of importing it
    # This ensures the server actually starts and stays running
    try:
        # Get the path to the app_final.py file
        app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_final.py')
        print(f"Starting application from: {app_path}")
        
        # Execute the app_final.py file directly
        subprocess.call([sys.executable, app_path])
    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()
    
if __name__ == "__main__":
    main()
