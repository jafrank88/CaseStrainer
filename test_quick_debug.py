#!/usr/bin/env python3
"""
Quick test to see debug logs
"""

import requests
import time
import json

def test_quick_debug():
    """Test with a quick debug check"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    pdf_path = r"D:\dev\casestrainer\sp-7788.pdf"
    
    print(f"Testing quick debug...")
    
    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    # Create file-like object for upload
    from io import BytesIO
    pdf_file = BytesIO(pdf_bytes)
    pdf_file.name = 'sp-7788.pdf'
    
    # Test with FORCED sync processing
    files = {'file': (pdf_file.name, pdf_file, 'application/pdf')}
    data = {
        'client_request_id': f'debug-test-{int(time.time())}',
        'force_mode': 'sync'
    }
    
    try:
        response = requests.post(f"{base_url}/analyze", files=files, data=data, timeout=300)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('result', {}).get('citations', [])
            print(f"Citations in response: {len(citations)}")
            
            if citations:
                print(f"First citation: {citations[0]}")
            else:
                print("No citations in response")
        else:
            print(f"❌ Upload failed: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_quick_debug()
