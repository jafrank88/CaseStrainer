#!/usr/bin/env python3
"""
Test script to verify the file upload fix is working.
"""

import requests
import json
import os

def test_file_upload_fix():
    """Test that file uploads now work correctly."""
    
    print("🧪 Testing File Upload Fix")
    print("=" * 50)
    
    # Test the production API
    base_url = "https://localhost/casestrainer/api"
    
    # Disable SSL verification for local testing
    session = requests.Session()
    session.verify = False
    
    # Path to the real PDF file
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print(f"📄 Testing PDF upload: {pdf_path}")
    print(f"📊 File size: {os.path.getsize(pdf_path)} bytes")
    print()
    
    try:
        # Upload the PDF file
        with open(pdf_path, 'rb') as f:
            files = {'file': ('gov.uscourts.wyd.64014.141.0_1.pdf', f, 'application/pdf')}
            
            response = session.post(
                f"{base_url}/analyze",
                files=files
            )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            
            print(f"✅ Upload successful!")
            print(f"📊 Found {len(citations)} citations")
            print(f"⏱️ Processing time: {result.get('processing_time', 'N/A')} seconds")
            
            # Show citation details
            for i, citation in enumerate(citations, 1):
                citation_text = citation.get('citation', '')
                case_name = citation.get('extracted_case_name', '')
                verified = citation.get('verified', False)
                source = citation.get('source', '')
                
                print(f"\nCitation {i}:")
                print(f"  Citation: {citation_text}")
                print(f"  Case Name: {case_name}")
                print(f"  Verified: {verified}")
                print(f"  Source: {source}")
                
                # Check for test citations
                if any(test_pattern in citation_text.lower() for test_pattern in ['123 f.3d 456', 'test citation', 'fake citation']):
                    print(f"  ⚠️ POTENTIAL TEST CITATION DETECTED!")
                else:
                    print(f"  ✅ Real citation")
                    
        elif response.status_code == 400:
            error_data = response.json()
            print(f"❌ Upload failed with 400 error:")
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
            print(f"   Request ID: {error_data.get('request_id', 'N/A')}")
            print(f"   Content Type: {error_data.get('content_type', 'N/A')}")
        else:
            print(f"❌ Upload failed with status {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    test_file_upload_fix() 