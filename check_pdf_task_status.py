#!/usr/bin/env python3
"""
Check task status for the PDF processing
"""

import requests
import time

def check_task_status():
    """Check the status of the PDF processing task"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    request_id = "96b14c67-e9ce-4777-a294-077b99101b61"  # From the last test
    
    print(f"Checking task status for: {request_id}")
    
    # Check task status
    status_response = requests.get(f"{base_url}/task_status/{request_id}")
    
    print(f"Status response: {status_response.status_code}")
    
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"Status: {status}")
    else:
        print(f"Error: {status_response.text}")
    
    # Also check verification status
    print(f"\n=== Verification Status ===")
    verification_response = requests.get(f"{base_url}/analyze/verification-status/{request_id}")
    
    print(f"Verification response: {verification_response.status_code}")
    
    if verification_response.status_code == 200:
        verification = verification_response.json()
        print(f"Verification: {verification}")
    else:
        print(f"Error: {verification_response.text}")

if __name__ == "__main__":
    check_task_status()
