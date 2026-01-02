#!/usr/bin/env python3
"""
Test async routing with a large document (simulating PDF content)
"""

import requests
import json

def test_large_document_async():
    """Test that large documents are routed to async processing"""
    
    # Create a large document (larger than 5KB threshold)
    large_text = """
    This is a test document that simulates a large PDF file.
    It contains legal citations and should be processed asynchronously.
    
    In City of Bellevue v. Lorang, 57 P.3d 273 (2002), the court considered city matters.
    In Berst v. Snohomish County, 114 Wn. App. 245 (2002), the court addressed county matters.
    
    """ * 200  # Repeat to make it large (about 12KB)
    
    print(f"🔍 Testing large document ({len(large_text)} characters)...")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": large_text, "extract_case_names": True}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 Processing Results:")
            print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
            print(f"Processing strategy: {result.get('metadata', {}).get('processing_strategy', 'unknown')}")
            print(f"Text length: {result.get('metadata', {}).get('text_length', 'unknown')}")
            
            if result.get('task_id'):
                print(f"✅ ASYNC PROCESSING: Task ID = {result.get('task_id')}")
                print("Large document correctly routed to async processing!")
            else:
                citations = result.get('citations', [])
                print(f"❌ SYNC PROCESSING: Found {len(citations)} citations")
                print("Large document was processed synchronously (this is wrong!)")
                
                # Show verification status
                verified_count = sum(1 for c in citations if c.get('verified', False))
                print(f"Verified citations: {verified_count}/{len(citations)}")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_small_document_sync():
    """Test that small documents are still processed synchronously"""
    
    small_text = """
    In City of Bellevue v. Lorang, 57 P.3d 273 (2002), the court considered city matters.
    In Berst v. Snohomish County, 114 Wn. App. 245 (2002), the court addressed county matters.
    """
    
    print(f"\n🔍 Testing small document ({len(small_text)} characters)...")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    data = {"text": small_text, "extract_case_names": True}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 Processing Results:")
            print(f"Processing mode: {result.get('metadata', {}).get('processing_mode', 'unknown')}")
            print(f"Processing strategy: {result.get('metadata', {}).get('processing_strategy', 'unknown')}")
            print(f"Text length: {result.get('metadata', {}).get('text_length', 'unknown')}")
            
            if result.get('task_id'):
                print(f"❌ ASYNC PROCESSING: Task ID = {result.get('task_id')}")
                print("Small document was routed to async (this is wrong!)")
            else:
                citations = result.get('citations', [])
                print(f"✅ SYNC PROCESSING: Found {len(citations)} citations")
                print("Small document correctly processed synchronously!")
                
                # Show verification status
                verified_count = sum(1 for c in citations if c.get('verified', False))
                print(f"Verified citations: {verified_count}/{len(citations)}")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_small_document_sync()
    test_large_document_async()
