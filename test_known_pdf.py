#!/usr/bin/env python3
"""Test with a known working legal PDF"""

import requests
import json
import time

def test_with_known_pdf():
    """Test with a known working legal PDF from CourtListener"""
    
    # Use a known CourtListener PDF
    pdf_url = "https://www.courtlistener.com/pdf/2024/01/05/22-1158.pdf"
    
    print(f"Testing with known PDF: {pdf_url}")
    
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
    
    # Now test through the API
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    data = {
        'type': 'url',
        'url': pdf_url,
        'force_mode': 'async',
        'enable_verification': 'false'
    }
    
    print(f"\nSubmitting to CaseStrainer API...")
    
    try:
        response = requests.post(api_url, json=data, timeout=30, verify=False)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('request_id')
            print(f"Task ID: {task_id}")
            
            if task_id:
                print("\nPolling for completion...")
                for i in range(24):  # 2 minutes max
                    time.sleep(5)
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
                        
                        print(f"Attempt {i+1}: Progress={progress}%, Status={status}, Message={message}")
                        
                        if status == 'completed':
                            print("\nSUCCESS!")
                            citations = status_data.get('citations', [])
                            clusters = status_data.get('clusters', [])
                            print(f"Found {len(citations)} citations and {len(clusters)} clusters")
                            
                            if citations:
                                print("\nFirst 3 citations:")
                                for i, citation in enumerate(citations[:3], 1):
                                    print(f"  {i}. {citation.get('citation', 'N/A')}")
                            
                            return True
                        elif status == 'failed':
                            print(f"\nFAILED: {status_data.get('message', 'Unknown error')}")
                            return False
                else:
                    print("\nTIMED OUT")
                    return False
        else:
            print(f"API Error: {response.status_code}")
            print(response.text[:500])
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_with_known_pdf()
    if success:
        print("\nHARMONIZED PIPELINE WORKS!")
    else:
        print("\nHARMONIZED PIPELINE STILL HAS ISSUES")
