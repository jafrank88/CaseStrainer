#!/usr/bin/env python3
"""
Simple test to check if the backend is running
"""

import requests
import os

def test_backend():
    """Test if the backend is running"""
    
    try:
        # Test health endpoint
        print("Testing health endpoint...")
        response = requests.get("http://localhost:5000/health", timeout=5)
        print(f"Health check status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Backend is running!")
            return True
        else:
            print(f"❌ Backend responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running or not accessible")
        return False
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def test_file_exists():
    """Test if the PDF file exists"""
    
    pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if os.path.exists(pdf_path):
        print(f"✅ File exists: {pdf_path}")
        print(f"📁 File size: {os.path.getsize(pdf_path)} bytes")
        return True
    else:
        print(f"❌ File not found: {pdf_path}")
        return False

if __name__ == "__main__":
    print("🧪 Simple backend test")
    print("=" * 30)
    
    # Test if file exists
    file_exists = test_file_exists()
    
    # Test if backend is running
    backend_running = test_backend()
    
    if file_exists and backend_running:
        print("\n✅ Ready to test PDF upload!")
    else:
        print("\n❌ Cannot proceed with test")
