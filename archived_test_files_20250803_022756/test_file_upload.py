#!/usr/bin/env python3
"""
Test script to verify file upload functionality
"""

import requests
import os

def test_file_upload():
    """Test file upload functionality"""
    
    # Test file path
    test_file_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        return False
    
    print(f"✅ Test file found: {test_file_path}")
    print(f"   File size: {os.path.getsize(test_file_path)} bytes")
    
    # Create FormData
    with open(test_file_path, 'rb') as f:
        files = {'file': (os.path.basename(test_file_path), f, 'application/pdf')}
        data = {'type': 'file'}
        
        print("📤 Sending file upload request...")
        
        try:
            response = requests.post(
                "https://wolf.law.uw.edu/casestrainer/api/analyze",
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ File upload successful!")
                print(f"   Citations found: {len(result.get('citations', []))}")
                print(f"   Clusters found: {len(result.get('clusters', []))}")
                
                # Show first citation if any
                if result.get('citations'):
                    first_citation = result['citations'][0]
                    print(f"   First citation: {first_citation.get('citation')}")
                    print(f"   Case name: {first_citation.get('extracted_case_name')}")
                    print(f"   Verified: {first_citation.get('verified')}")
                
                return True
            else:
                print(f"❌ File upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error during file upload: {e}")
            return False

def test_json_request():
    """Test JSON request to confirm the bug"""
    
    print("\n🧪 Testing JSON request (this should show the bug)...")
    
    payload = {
        'text': 'See Smith v. Jones, 123 F.3d 456 (2020)',
        'type': 'text'
    }
    
    try:
        response = requests.post(
            "https://wolf.law.uw.edu/casestrainer/api/analyze",
            json=payload,
            timeout=30
        )
        
        print(f"📥 JSON Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ JSON request successful!")
            print(f"   Citations found: {len(result.get('citations', []))}")
            
            # Show first citation if any
            if result.get('citations'):
                first_citation = result['citations'][0]
                print(f"   First citation: {first_citation.get('citation')}")
                print(f"   Case name: {first_citation.get('extracted_case_name')}")
                print(f"   Verified: {first_citation.get('verified')}")
            
            return True
        else:
            print(f"❌ JSON request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error during JSON request: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing CaseStrainer File Upload Functionality")
    print("=" * 50)
    
    # Test JSON request first (to confirm the bug)
    test_json_request()
    
    print("\n" + "=" * 50)
    
    # Test file upload
    test_file_upload()
    
    print("\n" + "=" * 50)
    print("�� Test completed") 