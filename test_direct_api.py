#!/usr/bin/env python3
"""
Test the API directly without going through the frontend
"""

import requests
import os

def test_direct_api():
    """Test the API directly"""
    
    print("🧪 Direct API Test")
    print("=" * 40)
    
    # Test the backend directly
    url = "http://localhost:5000/casestrainer/api/analyze"
    
    # PDF file path
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"📄 Testing with: {pdf_path}")
    print(f"📊 File size: {os.path.getsize(pdf_path)} bytes")
    print(f"🌐 URL: {url}")
    
    try:
        # Upload file directly to backend
        with open(pdf_path, 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            
            print("📤 Sending request...")
            response = requests.post(url, files=files, timeout=30)
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            result = response.json()
            print(f"📊 Citations found: {len(result.get('citations', []))}")
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("=" * 40)

if __name__ == "__main__":
    test_direct_api()
