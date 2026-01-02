#!/usr/bin/env python3
"""
Check if async task completes
"""

import requests
import time

def check_task_completion():
    """Check if our async task completes"""
    
    task_id = "4153917f-7164-477c-bd61-8afbd5511d55"
    url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
    
    for i in range(15):  # Check for 30 seconds
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"Attempt {i+1}: Status={data.get('status')}, Progress={data.get('progress_percent')}%, Citations={len(data.get('citations', []))}")
                
                if data.get('status') == 'completed':
                    print("✅ TASK COMPLETED!")
                    citations = data.get('citations', [])
                    print(f"Citations found: {len(citations)}")
                    for j, citation in enumerate(citations[:3]):
                        print(f"  {j+1}. {citation.get('citation')} - {citation.get('case_name')}")
                    break
                elif data.get('status') == 'failed':
                    print(f"❌ TASK FAILED: {data.get('error')}")
                    break
            else:
                print(f"Attempt {i+1}: Error {response.status_code}")
        except Exception as e:
            print(f"Attempt {i+1}: Error {e}")
        
        time.sleep(2)
    else:
        print("⏰ Task still not completed after 30 seconds")

if __name__ == "__main__":
    check_task_completion()
