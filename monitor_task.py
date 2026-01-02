#!/usr/bin/env python3
"""
Monitor the D2 59366-1-II task processing
"""

import requests
import json
import time

def monitor_task():
    """Monitor the task processing"""
    
    task_id = "94f7492c-f66f-42c8-9bf6-e4b1593376d1"
    
    print(f"🔍 Monitoring task: {task_id}")
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"Check {attempt}/{max_attempts}...")
        
        try:
            url = f"https://wolf.law.uw.edu/casestrainer/api/task/{task_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                
                print(f"Status: {status}")
                
                if status == 'completed':
                    print(f"✅ Task completed!")
                    
                    task_result = result.get('result', {})
                    citations = task_result.get('citations', [])
                    clusters = task_result.get('clusters', [])
                    
                    print(f"Citations found: {len(citations)}")
                    print(f"Clusters found: {len(clusters)}")
                    
                    if citations:
                        print(f"\n📋 First 5 citations:")
                        for i, citation in enumerate(citations[:5]):
                            print(f"{i+1}. {citation.get('citation', 'N/A')}")
                            print(f"   Extracted: '{citation.get('extracted_case_name', 'N/A')}', {citation.get('extracted_date', 'N/A')}")
                            print(f"   Verified: {citation.get('verified', False)}")
                            print(f"   Source: {citation.get('verification_source', 'N/A')}")
                    
                    # Save results
                    output_file = r"d:\dev\casestrainer\D2_59366_fixed_results.json"
                    try:
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(task_result, f, indent=2, ensure_ascii=False)
                        print(f"\n💾 Results saved to: {output_file}")
                    except Exception as e:
                        print(f"\n❌ Failed to save results: {e}")
                    
                    return
                
                elif status == 'failed':
                    error_msg = result.get('error', 'Unknown error')
                    print(f"❌ Task failed: {error_msg}")
                    return
                
                elif status == 'processing':
                    progress = result.get('progress', {})
                    if progress:
                        current_step = progress.get('current_step', 'Unknown')
                        print(f"   Current step: {current_step}")
                
            else:
                print(f"❌ Status check failed: {response.status_code}")
            
        except Exception as e:
            print(f"❌ Error checking status: {e}")
        
        time.sleep(10)
    
    print(f"❌ Timeout: Task did not complete within {max_attempts * 10} seconds")

if __name__ == "__main__":
    monitor_task()
