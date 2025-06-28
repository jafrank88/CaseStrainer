#!/usr/bin/env python3
"""
Test script to compare backend API processing of URL vs text.
"""

import requests
import json
import time

def test_backend_url_vs_text():
    """Compare backend API processing of URL vs text."""
    print("Testing Backend API: URL vs Text Processing")
    print("=" * 60)
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Test health endpoint first
    print("1. Checking backend health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # Test URL processing
    print("\n2. Testing URL processing via API:")
    print("-" * 40)
    
    url_data = {
        'type': 'url',
        'url': 'https://www.law.cornell.edu/supct/html/02-102.ZS.html'
    }
    
    try:
        response = requests.post(f"{base_url}/analyze", json=url_data)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ URL upload accepted, task ID: {task_id}")
            
            # Wait for completion
            if task_id:
                for i in range(10):  # Wait up to 10 seconds
                    time.sleep(1)
                    status_response = requests.get(f"{base_url}/task_status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'completed':
                            citations = status_data.get('citations', [])
                            case_names = status_data.get('case_names', [])
                            print(f"   Status: {status_data.get('status')}")
                            print(f"   Citations found: {len(citations)}")
                            print(f"   Case names found: {len(case_names)}")
                            if citations:
                                print("   Sample citations:")
                                for i, citation in enumerate(citations[:3]):
                                    print(f"     {i+1}. {citation.get('citation', 'N/A')}")
                            break
                        elif status_data.get('status') == 'failed':
                            print(f"   Status: {status_data.get('status')}")
                            print(f"   Error: {status_data.get('error', 'Unknown error')}")
                            break
                else:
                    print("   Timeout waiting for completion")
        else:
            print(f"❌ URL upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing URL upload: {str(e)}")
    
    # Test text processing
    print("\n3. Testing text processing via API:")
    print("-" * 40)
    
    text_content = """
    This document contains citations like Brown v. Board of Education, 347 U.S. 483 (1954).
    Another citation: Roe v. Wade, 410 U.S. 113 (1973).
    Washington case: State v. Smith, 123 Wn.2d 456 (1994).
    """
    
    text_data = {
        'type': 'text',
        'text': text_content
    }
    
    try:
        response = requests.post(f"{base_url}/analyze", json=text_data)
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ Text upload accepted, task ID: {task_id}")
            
            # Wait for completion
            if task_id:
                for i in range(10):  # Wait up to 10 seconds
                    time.sleep(1)
                    status_response = requests.get(f"{base_url}/task_status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'completed':
                            citations = status_data.get('citations', [])
                            case_names = status_data.get('case_names', [])
                            print(f"   Status: {status_data.get('status')}")
                            print(f"   Citations found: {len(citations)}")
                            print(f"   Case names found: {len(case_names)}")
                            if citations:
                                print("   Sample citations:")
                                for i, citation in enumerate(citations[:3]):
                                    print(f"     {i+1}. {citation.get('citation', 'N/A')}")
                            break
                        elif status_data.get('status') == 'failed':
                            print(f"   Status: {status_data.get('status')}")
                            print(f"   Error: {status_data.get('error', 'Unknown error')}")
                            break
                else:
                    print("   Timeout waiting for completion")
        else:
            print(f"❌ Text upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing text upload: {str(e)}")
    
    print("\n4. Summary:")
    print("-" * 40)
    print("This test compares how the backend API processes URLs vs text.")
    print("If there are differences, it could be due to:")
    print("- Different processing paths in the API")
    print("- Different validation or preprocessing")
    print("- Different error handling")

if __name__ == "__main__":
    test_backend_url_vs_text() 