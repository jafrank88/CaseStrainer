#!/usr/bin/env python
"""
Production deployment script for CaseStrainer
Uses Cheroot as a production-ready WSGI server
Also checks and ensures Nginx is running for proper proxying
"""
import os
import sys
import subprocess
import traceback
import time
import socket
import re
import shutil

def check_nginx_running():
    """Check if Nginx is running and start it if it's not."""
    # Path to Windows Nginx installation
    nginx_path = r"C:\Users\jafrank\Downloads\nginx-1.27.5\nginx-1.27.5\nginx.exe"
    
    # Check if Nginx executable exists
    if not os.path.exists(nginx_path):
        print(f"Warning: Nginx executable not found at {nginx_path}")
        return False
    
    # Check if Nginx is already running
    try:
        # Check for Nginx process
        nginx_running = False
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq nginx.exe'], 
                              capture_output=True, text=True, check=False)
        if 'nginx.exe' in result.stdout:
            print("Nginx is already running.")
            nginx_running = True
        
        # Also check if Docker Nginx is running
        result = subprocess.run(['docker', 'ps', '|', 'findstr', 'nginx'], 
                              capture_output=True, text=True, shell=True, check=False)
        if 'docker-nginx-1' in result.stdout:
            print("Docker Nginx container is running.")
            return True  # Docker Nginx is sufficient
        
        # If neither is running, start Windows Nginx
        if not nginx_running:
            print("Nginx is not running. Starting Nginx...")
            # Start Nginx
            subprocess.Popen([nginx_path], 
                           cwd=os.path.dirname(nginx_path),
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Wait for Nginx to start
            time.sleep(2)
            
            # Verify Nginx started successfully
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq nginx.exe'], 
                                  capture_output=True, text=True, check=False)
            if 'nginx.exe' in result.stdout:
                print("Nginx started successfully.")
                return True
            else:
                print("Failed to start Nginx.")
                return False
        return True
    except Exception as e:
        print(f"Error checking/starting Nginx: {e}")
        return False

def check_port_available(port):
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) != 0

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
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on (default: 5001)')
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
    
    # Check if the specified port is available
    if not check_port_available(args.port):
        print(f"Warning: Port {args.port} is already in use. CaseStrainer may not start properly.")
        print("Attempting to kill any existing Python processes...")
        try:
            subprocess.run(['taskkill', '/f', '/im', 'python.exe'], check=False)
            time.sleep(2)  # Give processes time to terminate
        except Exception as e:
            print(f"Error killing Python processes: {e}")
    
    # Check and ensure Nginx is running
    print("\nChecking Nginx status...")
    nginx_status = check_nginx_running()
    if nginx_status:
        print("Nginx check passed. Proceeding with CaseStrainer startup.")
    else:
        print("Warning: Nginx may not be running properly. External access through https://wolf.law.uw.edu/casestrainer/ might not work.")
        print(f"However, CaseStrainer will still be accessible locally at http://127.0.0.1:{args.port}")
        user_input = input("Do you want to continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            print("Startup aborted by user.")
            return
    
    # Run the application directly instead of importing it
    # This ensures the server actually starts and stays running
    try:
        # Get the path to the app_final.py file
        app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_final.py')
        print(f"\nStarting application from: {app_path}")
        
        # Execute the app_final.py file directly
        subprocess.call([sys.executable, app_path])
    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()
    
if __name__ == "__main__":
    main()
