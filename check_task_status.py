#!/usr/bin/env python3
"""
Check the status of the async task to see if it completed.
"""

import requests
import time

def check_task_status():
    """Check the status of recent async tasks."""
    
    # The task ID from the previous test
    task_id = "6195dd77-9df0-47b3-ad8d-04fcdaf44a1f"
    
    print(f"🔍 Checking status of task: {task_id}")
    
    try:
        response = requests.get(
            f"http://localhost:8080/casestrainer/api/task_status/{task_id}",
            timeout=10
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"🔍 Task status: {data.get('status')}")
            print(f"📊 Citations found: {len(data.get('citations', []))}")
            print(f"🔗 Clusters found: {len(data.get('clusters', []))}")
            
            if data.get('citations'):
                print("\n📋 Citations found:")
                for i, citation in enumerate(data['citations'][:5]):
                    print(f"  {i+1}. {citation.get('citation', 'N/A')} - {citation.get('extracted_case_name', 'N/A')}")
            
            if data.get('status') == 'failed':
                print(f"🚨 Task failed: {data.get('error')}")
                
        elif response.status_code == 404:
            print("❌ Task not found (may have expired)")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except Exception as e:
        print(f"💥 Check failed: {e}")

if __name__ == "__main__":
    check_task_status()
