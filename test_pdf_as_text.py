#!/usr/bin/env python3
"""Test processing the PDF content as text directly"""

import requests
import json
import time

def test_pdf_as_text():
    """Test processing the PDF content as text without verification"""
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    # Download the PDF content first
    pdf_url = "https://www.courts.wa.gov/opinions/pdf/863215.pdf"
    print(f"Downloading PDF from: {pdf_url}")
    
    try:
        # Download PDF
        pdf_response = requests.get(pdf_url, timeout=30, verify=False)
        if pdf_response.status_code != 200:
            print(f"Failed to download PDF: {pdf_response.status_code}")
            return False
        
        # Extract text from PDF
        import io
        try:
            import pypdf
        except ImportError:
            import PyPDF2 as pypdf
        
        pdf_file = io.BytesIO(pdf_response.content)
        pdf_reader = pypdf.PdfReader(pdf_file)
        
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        print(f"Extracted {len(text)} characters from PDF")
        
        # Take first 10000 characters to test
        test_text = text[:10000]
        print(f"Testing with first {len(test_text)} characters...")
        
        # Test data
        data = {
            'type': 'text',
            'text': test_text,
            'force_mode': 'async',
            'enable_verification': 'false'  # Disable verification
        }
        
        print(f"Force mode: {data['force_mode']}")
        print(f"Verification: {data['enable_verification']}")
        
        # Submit the request
        print("\nSubmitting request...")
        response = requests.post(url, json=data, timeout=30, verify=False)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('request_id')
            print(f"Task ID: {task_id}")
            print(f"Initial status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            
            # Poll for completion
            if task_id:
                print("\nPolling for task completion...")
                for i in range(30):  # Max 2.5 minutes
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
                            print("\nTask completed successfully!")
                            citations = status_data.get('citations', [])
                            clusters = status_data.get('clusters', [])
                            print(f"Found {len(citations)} citations and {len(clusters)} clusters")
                            
                            # Show citations
                            if citations:
                                print("\nCitations found:")
                                for i, citation in enumerate(citations[:5], 1):  # Show first 5
                                    print(f"  {i}. {citation.get('citation', 'N/A')}")
                            
                            return True
                        elif status == 'failed':
                            print(f"\nTask failed: {status_data.get('message', 'Unknown error')}")
                            return False
                    else:
                        print(f"Status check failed: {status_response.status_code}")
                else:
                    print("\nTask timed out after 2.5 minutes")
                    return False
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:1000])
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_as_text()
    if success:
        print("\nTest passed - PDF text processing works")
    else:
        print("\nTest failed")
