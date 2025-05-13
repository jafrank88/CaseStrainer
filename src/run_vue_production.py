#!/usr/bin/env python
"""
Production deployment script for CaseStrainer with Vue.js frontend
Uses the same approach as run_production.py but for the Vue.js version
"""
import os
import sys
import subprocess
import traceback
import time
import socket
import re
import shutil
import argparse

def check_port_available(port):
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return True
    except socket.error:
        return False

def build_vue_frontend():
    """Build the Vue.js frontend if Node.js is available."""
    print("Checking if Vue.js frontend needs to be built...")
    
    # Check if the static/vue directory exists and contains the necessary files
    vue_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'vue')
    if os.path.exists(vue_dir) and os.path.exists(os.path.join(vue_dir, 'index.html')):
        print("Vue.js frontend is already built.")
        return True
    
    print("Vue.js frontend needs to be built.")
    
    # Check if Node.js is available
    try:
        # Try to run npm to check if Node.js is installed
        npm_path = shutil.which('npm')
        if npm_path:
            print(f"Found npm at: {npm_path}")
        else:
            print("npm not found in PATH. Checking common installation directories...")
            # Check common installation directories for npm
            common_paths = [
                r"C:\Program Files\nodejs\npm.cmd",
                r"C:\Program Files (x86)\nodejs\npm.cmd",
                os.path.expanduser("~\\AppData\\Roaming\\npm\\npm.cmd")
            ]
            for path in common_paths:
                if os.path.exists(path):
                    npm_path = path
                    print(f"Found npm at: {npm_path}")
                    break
        
        if not npm_path:
            print("npm not found. Cannot build Vue.js frontend.")
            return False
        
        # Navigate to the Vue.js project directory
        vue_project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'casestrainer-vue')
        if not os.path.exists(vue_project_dir):
            print(f"Vue.js project directory not found at: {vue_project_dir}")
            return False
        
        print(f"Building Vue.js frontend from: {vue_project_dir}")
        
        # Install dependencies
        print("Installing dependencies...")
        os.chdir(vue_project_dir)
        subprocess.check_call([npm_path, 'install'])
        
        # Build the Vue.js frontend
        print("Building Vue.js frontend...")
        subprocess.check_call([npm_path, 'run', 'build'])
        
        # Check if the build was successful
        dist_dir = os.path.join(vue_project_dir, 'dist')
        if not os.path.exists(dist_dir) or not os.path.exists(os.path.join(dist_dir, 'index.html')):
            print("Vue.js frontend build failed.")
            return False
        
        # Create static/vue directory if it doesn't exist
        if not os.path.exists(vue_dir):
            os.makedirs(vue_dir)
        
        # Copy the built files to the static/vue directory
        print("Copying built files to static/vue directory...")
        for item in os.listdir(dist_dir):
            src = os.path.join(dist_dir, item)
            dst = os.path.join(vue_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        
        print("Vue.js frontend built and copied successfully.")
        return True
    
    except Exception as e:
        print(f"Error building Vue.js frontend: {e}")
        traceback.print_exc()
        return False

def main():
    """Run the CaseStrainer application with Vue.js frontend in production mode."""
    print("Starting CaseStrainer with Vue.js frontend in production mode...")
    
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
    parser = argparse.ArgumentParser(description='Run CaseStrainer with Vue.js frontend in production mode')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on (default: 5000)')
    parser.add_argument('--skip-build', action='store_true', help='Skip building the Vue.js frontend')
    args = parser.parse_args()
    
    # Set host and port environment variables
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
    
    # Build the Vue.js frontend if needed
    if not args.skip_build:
        build_result = build_vue_frontend()
        if not build_result:
            print("Warning: Vue.js frontend build failed or was skipped.")
            print("The application will still start, but the Vue.js frontend may not be available.")
    
    # Run the application directly instead of importing it
    try:
        # Get the path to the app_final_vue.py file
        app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_final_vue.py')
        print(f"\nStarting application from: {app_path}")
        
        # Execute the app_final_vue.py file directly
        subprocess.call([sys.executable, app_path, '--host', args.host, '--port', str(args.port)])
    except Exception as e:
        print(f"Error starting application: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
