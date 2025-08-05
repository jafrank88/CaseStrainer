#!/usr/bin/env python3
"""
Test file upload functionality
"""

import requests
import json

def test_file_upload():
    """Test file upload with the fixed upload directory"""
    print("Testing file upload functionality...")
    
    # Test file upload
    with open('gov.uscourts.wyd.64014.141.0_1.pdf', 'rb') as f:
        files = {'file': ('gov.uscourts.wyd.64014.141.0_1.pdf', f, 'application/pdf')}
        data = {'type': 'file'}
        
        try:
            response = requests.post(
                'http://localhost:5000/casestrainer/api/analyze',
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ File upload successful!")
                print(f"Citations found: {len(result.get('citations', []))}")
                print(f"Clusters found: {len(result.get('clusters', []))}")
            else:
                print("❌ File upload failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_file_upload() 