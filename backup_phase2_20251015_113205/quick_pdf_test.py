#!/usr/bin/env python3
"""
Quick test for PDF processing with timeout.
"""

import requests
import time
from requests_toolbelt.multipart.encoder import MultipartEncoder

def test_pdf_processing(pdf_path, timeout=30):
    """Test PDF processing with a timeout."""
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    # Prepare the multipart form data
    multipart_data = MultipartEncoder(
        fields={
            'file': (pdf_path.split('\\')[-1], open(pdf_path, 'rb'), 'application/pdf'),
            'type': 'file',
        }
    )
    
    # Set up headers
    headers = {
        'Content-Type': multipart_data.content_type,
        'Accept': 'application/json',
    }
    
    print(f"Sending {pdf_path} for processing...")
    start_time = time.time()
    
    try:
        # Send the request with a timeout
        response = requests.post(
            api_url, 
            data=multipart_data, 
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()
        
        # If we get a task ID, try to get results with a short delay
        if 'request_id' in result and result.get('status') != 'completed':
            task_id = result['request_id']
            print(f"Task queued. Polling for results (ID: {task_id})...")
            
            # Short delay before polling
            time.sleep(2)
            
            # Poll for results
            status_url = f"https://wolf.law.uw.edu/casestrainer/api/status/{task_id}"
            response = requests.get(status_url, timeout=timeout)
            result = response.json()
        
        # Process the result
        process_time = time.time() - start_time
        print(f"\n=== Results ({process_time:.2f} seconds) ===")
        
        if 'citations' in result:
            citations = result['citations']
            print(f"Found {len(citations)} citations:")
            
            for i, cite in enumerate(citations[:5], 1):  # Show first 5 citations
                print(f"{i}. {cite.get('citation', 'N/A')}")
                print(f"   Case: {cite.get('case_name', 'N/A')}")
                print(f"   Page: {cite.get('page', 'N/A')}\n")
            
            if len(citations) > 5:
                print(f"... and {len(citations) - 5} more citations.")
        else:
            print("No citations found in the response.")
        
        # Save full result
        with open('quick_test_result.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\nFull results saved to quick_test_result.json")
        
        return result
        
    except requests.exceptions.Timeout:
        print(f"Error: Request timed out after {timeout} seconds.")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            print(f"Response: {e.response.text[:500]}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    return None

if __name__ == "__main__":
    pdf_path = r"D:\dev\casestrainer\1033940.pdf"
    test_pdf_processing(pdf_path)
