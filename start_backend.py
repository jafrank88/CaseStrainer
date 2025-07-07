#!/usr/bin/env python3
"""
Simple script to start the CaseStrainer backend server for testing
"""

import os
import sys
import subprocess
import time
import requests

def start_backend():
    """Start the backend server"""
    print("🚀 Starting CaseStrainer backend server...")
    
    try:
        # Add the src directory to the Python path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
        
        # Import and create the app
        from app_final_vue import create_app
        
        app = create_app()
        
        print("✅ Backend server created successfully")
        print("🌐 Starting Flask development server on http://localhost:5000")
        print("📝 Press Ctrl+C to stop the server")
        
        # Start the application
        app.run(host="0.0.0.0", port=5000, debug=True)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the correct directory and have all dependencies installed")
        return False
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return False

def check_backend_health():
    """Check if the backend is running"""
    try:
        response = requests.get("http://localhost:5000/casestrainer/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

if __name__ == "__main__":
    print("🧪 CaseStrainer Backend Starter")
    print("=" * 40)
    
    # Check if backend is already running
    if check_backend_health():
        print("✅ Backend is already running!")
        print("🌐 Health check: http://localhost:5000/casestrainer/api/health")
        print("📊 You can now run: python test_pdf_direct.py")
    else:
        print("🚀 Starting backend server...")
        start_backend() 