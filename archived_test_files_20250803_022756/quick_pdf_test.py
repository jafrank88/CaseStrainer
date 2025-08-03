#!/usr/bin/env python3
"""
Quick PDF test with running Flask server
"""

import requests
import os
import json

def main():
    print("🧪 Quick PDF Test")
    print("=" * 30)
    
    # Check if file exists
    pdf_path = "gov.uscourts.wyd.64014.141.0_1.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"✅ File exists: {pdf_path}")
    print(f"📁 File size: {os.path.getsize(pdf_path)} bytes")
    
    # Test health endpoint
    try:
        print("\n🌐 Testing server health...")
        response = requests.get("http://10.158.120.151:5000/casestrainer/api/health", timeout=10)
        print(f"Health status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server is healthy")
        else:
            print(f"❌ Server health check failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test file upload
    try:
        print(f"\n📤 Uploading PDF file...")
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path, f, 'application/pdf')}
            response = requests.post(
                "http://10.158.120.151:5000/casestrainer/api/analyze",
                files=files,
                timeout=30
            )
        
        print(f"Upload status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"📋 Task ID: {result.get('task_id')}")
            print(f"📝 Message: {result.get('message')}")
            print(f"📊 Status: {result.get('status')}")
            
            # Show metadata
            metadata = result.get('metadata', {})
            if metadata:
                print(f"📋 Metadata:")
                for key, value in metadata.items():
                    print(f"   {key}: {value}")
            
            # Poll for results
            task_id = result.get('task_id')
            if task_id:
                print(f"\n🔄 Polling for results...")
                poll_for_results(task_id)
            
        else:
            print(f"❌ Upload failed!")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Upload failed: {e}")

def poll_for_results(task_id):
    """Poll for task completion"""
    import time
    
    for attempt in range(10):  # Try 10 times
        try:
            print(f"  Polling attempt {attempt + 1}...")
            response = requests.get(
                f"http://10.158.120.151:5000/casestrainer/api/task_status/{task_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                print(f"    Status: {status}")
                
                if status == 'completed':
                    print("✅ Task completed!")
                    show_results(result)
                    return True
                elif status == 'failed':
                    print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
                    return False
                elif status == 'processing':
                    print("    Still processing...")
                else:
                    print(f"    Unknown status: {status}")
            else:
                print(f"    Status check failed: {response.status_code}")
            
        except Exception as e:
            print(f"    Polling error: {e}")
        
        time.sleep(3)  # Wait 3 seconds between attempts
    
    print("⏰ Timeout waiting for results")

def show_results(result):
    """Show the results"""
    results = result.get('results', {})
    if not results:
        print("📋 No results found")
        return
    
    print(f"\n📋 Results Summary:")
    print(f"   Total citations: {results.get('total_citations', 0)}")
    print(f"   Verified citations: {results.get('verified_citations', 0)}")
    print(f"   Unverified citations: {results.get('unverified_citations', 0)}")
    
    citations = results.get('citations', [])
    if citations:
        print(f"\n📚 Found {len(citations)} citations:")
        for i, citation in enumerate(citations, 1):
            print(f"  {i}. {citation.get('citation', 'Unknown')}")
            print(f"     Verified: {citation.get('verified', 'Unknown')}")
            if citation.get('case_name'):
                print(f"     Case: {citation.get('case_name')}")
            if citation.get('court'):
                print(f"     Court: {citation.get('court')}")
            print()
    else:
        print(f"\n📚 No citations found in the document")

if __name__ == "__main__":
    main() 