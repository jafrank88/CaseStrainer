#!/usr/bin/env python3
"""
Quick file upload test with short timeout
"""

import requests
import os

def test_quick_upload():
    """Test file upload with short timeout"""
    
    print("🧪 Quick File Upload Test")
    print("=" * 40)
    
    # Test the backend directly with short timeout
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # PDF file path
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"📄 Testing with: {pdf_path}")
    print(f"📊 File size: {os.path.getsize(pdf_path)} bytes")
    print(f"🌐 URL: {url}")
    print(f"⏱️  Timeout: 10 seconds")
    
    try:
        # Upload file with short timeout
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            
            print("📤 Sending request...")
            response = requests.post(url, files=files, timeout=10)
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            result = response.json()
            print(f"📊 Citations found: {len(result.get('citations', []))}")
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ TIMEOUT: Request timed out after 10 seconds")
        print("💡 This suggests the backend is busy processing another file")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("=" * 40)

if __name__ == "__main__":
    test_quick_upload() 