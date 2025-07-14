#!/usr/bin/env python3
"""Test the API endpoint to see if it's calling the extraction function correctly"""

import requests
import json

def test_api():
    base_url = "http://localhost:5001/casestrainer/api"
    
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health status: {response.status_code}")
        print(f"Health response: {response.json()}")
    except Exception as e:
        print(f"Health test failed: {e}")
    
    # Test analyze endpoint with text
    print("\nTesting analyze endpoint with text...")
    try:
        data = {
            "type": "text",
            "text": "The court in Smith v. Jones, 123 U.S. 456 (2020) held that..."
        }
        response = requests.post(f"{base_url}/analyze", json=data)
        print(f"Analyze status: {response.status_code}")
        print(f"Analyze response: {response.json()}")
    except Exception as e:
        print(f"Analyze test failed: {e}")
    
    # Test analyze endpoint with file (should not return 501)
    print("\nTesting analyze endpoint with file...")
    try:
        # Create a simple text file
        with open("test_file.txt", "w") as f:
            f.write("This is a test file with a citation: Smith v. Jones, 123 U.S. 456 (2020)")
        
        with open("test_file.txt", "rb") as f:
            files = {"file": ("test_file.txt", f, "text/plain")}
            response = requests.post(f"{base_url}/analyze", files=files)
        
        print(f"File analyze status: {response.status_code}")
        print(f"File analyze response: {response.json()}")
        
        # Clean up
        import os
        os.remove("test_file.txt")
    except Exception as e:
        print(f"File analyze test failed: {e}")

if __name__ == "__main__":
    test_api() 