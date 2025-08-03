#!/usr/bin/env python3
"""
Final file upload test with longer timeout for synchronous processing
"""

import requests
import os

def test_file_upload_final():
    """Test file upload with longer timeout"""
    
    print("🧪 Final File Upload Test")
    print("=" * 40)
    
    # Test the backend directly with longer timeout
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # PDF file path
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"📄 Testing with: {pdf_path}")
    print(f"📊 File size: {os.path.getsize(pdf_path)} bytes")
    print(f"🌐 URL: {url}")
    print(f"⏱️  Timeout: 120 seconds (for synchronous processing)")
    
    try:
        # Upload file with longer timeout
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            
            print("📤 Sending request...")
            response = requests.post(url, files=files, timeout=120)
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            result = response.json()
            print(f"📊 Citations found: {len(result.get('citations', []))}")
            print(f"📊 Clusters found: {len(result.get('clusters', []))}")
            print(f"⏱️  Processing time: {result.get('processing_time', 'N/A')}")
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT: Request timed out after 120 seconds")
        print("💡 The file is being processed but taking longer than expected")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("=" * 40)

if __name__ == "__main__":
    test_file_upload_final() 