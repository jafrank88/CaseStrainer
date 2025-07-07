#!/usr/bin/env python3
import requests
import json
import time

def test_api():
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health endpoint: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Health endpoint error: {e}")
    
    # Test analyze endpoint with sample data
    sample_data = {
        "text": "The court in Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, held that...",
        "source": "Test"
    }
    
    try:
        response = requests.post(f"{base_url}/analyze", 
                               json=sample_data, 
                               timeout=30)
        print(f"\nAnalyze endpoint: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Analyze endpoint error: {e}")

if __name__ == "__main__":
    test_api() 