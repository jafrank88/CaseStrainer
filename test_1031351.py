#!/usr/bin/env python3
"""Test with the 1031351.pdf file"""

import requests
import json
import time
import os

def test_with_1031351():
    """Test with 1031351.pdf from Washington State Courts"""
    
    # Try to download the PDF
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/1031351.pdf"
    
    print(f"Testing with PDF: {pdf_url}")
    
    # First verify the PDF is accessible
    try:
        head_response = requests.head(pdf_url, timeout=10, verify=False)
        print(f"PDF Status: {head_response.status_code}")
        print(f"Content-Type: {head_response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {head_response.headers.get('Content-Length', 'N/A')}")
        
        if head_response.status_code != 200:
            print("PDF not accessible")
            return False
    except Exception as e:
        print(f"Error checking PDF: {e}")
        return False
    
    # Download the PDF to test file upload as well
    print("\nDownloading PDF for file upload test...")
    try:
        response = requests.get(pdf_url, timeout=30, verify=False)
        response.raise_for_status()
        
        # Save to temp file
        temp_file = "d:\\dev\\casestrainer\\temp_1031351.pdf"
        with open(temp_file, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded {len(response.content)} bytes to {temp_file}")
        
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        temp_file = None
    
    # Test URL processing first
    print("\n=== Testing URL Processing ===")
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    data = {
        'type': 'url',
        'url': pdf_url,
        'force_mode': 'async',
        'enable_verification': 'false'
    }
    
    try:
        response = requests.post(api_url, json=data, timeout=30, verify=False)
        
        print(f"URL Submit Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('request_id')
            print(f"Task ID: {task_id}")
            
            if task_id:
                print("\nPolling for URL processing completion...")
                url_success = poll_task(task_id, "URL")
                
                if not url_success:
                    print("URL processing failed or timed out")
        else:
            print(f"URL API Error: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"URL processing exception: {e}")
    
    # Test file upload if we downloaded the file
    if temp_file and os.path.exists(temp_file):
        print("\n=== Testing File Upload ===")
        
        try:
            with open(temp_file, 'rb') as f:
                files = {'file': f}
                form_data = {
                    'force_mode': 'async',
                    'enable_verification': 'false'
                }
                
                response = requests.post(
                    api_url,
                    files=files,
                    data=form_data,
                    timeout=30,
                    verify=False
                )
                
                print(f"File Upload Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    task_id = result.get('request_id')
                    print(f"Task ID: {task_id}")
                    
                    if task_id:
                        print("\nPolling for file upload completion...")
                        file_success = poll_task(task_id, "File")
                        
                        if not file_success:
                            print("File upload processing failed or timed out")
                else:
                    print(f"File API Error: {response.status_code}")
                    print(response.text[:500])
                    
        except Exception as e:
            print(f"File upload exception: {e}")
        
        # Clean up temp file
        try:
            os.remove(temp_file)
            print(f"\nCleaned up temp file: {temp_file}")
        except:
            pass
    
    return True

def poll_task(task_id, task_type):
    """Poll for task completion"""
    
    for i in range(36):  # 3 minutes max
        time.sleep(5)
        try:
            status_response = requests.get(
                f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}",
                timeout=10,
                verify=False
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                progress = status_data.get('progress_percent', 0)
                message = status_data.get('current_message', '')
                status = status_data.get('status', '')
                
                print(f"  {task_type} Attempt {i+1}: Progress={progress}%, Status={status}, Message={message}")
                
                if status == 'completed':
                    print(f"\n{task_type} Processing SUCCESS!")
                    citations = status_data.get('citations', [])
                    clusters = status_data.get('clusters', [])
                    print(f"  Found {len(citations)} citations and {len(clusters)} clusters")
                    
                    if citations:
                        print(f"\n  First 3 citations from {task_type}:")
                        for i, citation in enumerate(citations[:3], 1):
                            print(f"    {i}. {citation.get('citation', 'N/A')}")
                    
                    return True
                elif status == 'failed':
                    print(f"\n{task_type} Processing FAILED: {status_data.get('message', 'Unknown error')}")
                    return False
            else:
                print(f"  {task_type} Status check failed: {status_response.status_code}")
                
        except Exception as e:
            print(f"  {task_type} Status check error: {e}")
    
    print(f"\n{task_type} Processing TIMED OUT")
    return False

if __name__ == "__main__":
    test_with_1031351()
