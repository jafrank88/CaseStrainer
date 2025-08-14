"""
Test script to verify the /analyze endpoint functionality for different input types.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"  # Update if your server is running on a different host/port
TEST_TEXT = "The court in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) ruled that..."
TEST_URL = "https://caselaw.findlaw.com/court/us-supreme-court/19-7.html"
TEST_PDF_PATH = "test_document.pdf"  # Path to a test PDF file

# Test data
TEST_CASES = [
    {
        "name": "Text Input",
        "type": "text",
        "data": {"text": TEST_TEXT, "type": "text"}
    },
    {
        "name": "URL Input",
        "type": "url",
        "data": {"url": TEST_URL, "type": "url"}
    },
    {
        "name": "File Upload",
        "type": "file",
        "data": None,  # Will be handled specially
        "file_path": TEST_PDF_PATH
    }
]

def test_text_analysis():
    """Test text analysis endpoint."""
    print("\n=== Testing Text Analysis ===")
    url = f"{BASE_URL}/api/analyze"
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(
            url,
            json={"text": TEST_TEXT, "type": "text"},
            headers=headers,
            timeout=30
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Found {len(result.get('citations', []))} citations.")
            print(f"Processing time: {result.get('processing_time', 'N/A')}s")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing text analysis: {str(e)}")

def test_url_analysis():
    """Test URL analysis endpoint."""
    print("\n=== Testing URL Analysis ===")
    url = f"{BASE_URL}/api/analyze"
    
    try:
        response = requests.post(
            url,
            json={"url": TEST_URL, "type": "url"},
            timeout=60  # Allow more time for URL processing
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'task_id' in result:
                print(f"Task queued. Task ID: {result['task_id']}")
                # You would typically poll for task status here
            else:
                print(f"Success! Found {len(result.get('citations', []))} citations.")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing URL analysis: {str(e)}")

def test_file_analysis():
    """Test file upload and analysis."""
    print("\n=== Testing File Upload ===")
    url = f"{BASE_URL}/api/analyze"
    
    if not os.path.exists(TEST_PDF_PATH):
        print(f"Test file not found: {TEST_PDF_PATH}")
        return
    
    try:
        with open(TEST_PDF_PATH, 'rb') as f:
            files = {'file': (os.path.basename(TEST_PDF_PATH), f, 'application/pdf')}
            response = requests.post(
                url,
                files=files,
                data={'type': 'file'},
                timeout=120  # Allow more time for file processing
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'task_id' in result:
                print(f"Task queued. Task ID: {result['task_id']}")
                # You would typically poll for task status here
            else:
                print(f"Success! Found {len(result.get('citations', []))} citations.")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error testing file upload: {str(e)}")

def main():
    """Run all test cases."""
    print("=== Starting API Endpoint Tests ===")
    
    # Test text analysis
    test_text_analysis()
    
    # Test URL analysis
    test_url_analysis()
    
    # Test file upload
    test_file_analysis()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
