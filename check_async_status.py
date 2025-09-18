"""
Check Async Processing Status
Checks the status of the async task that was started.
"""

import requests
import time

def check_async_status():
    """Check the status of the async processing task."""
    
    # The task ID from the previous run (you'll need to update this)
    task_id = "9b44ab9d-d595-4843-8d2a-f198d118c"  # Update with actual task ID
    
    print(f"🔍 Checking status of async task: {task_id}")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            status_url = f"http://localhost:8080/casestrainer/api/analyze/verification-results/{task_id}"
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                
                print(f"Attempt {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    citations = data.get('citations', [])
                    
                    print(f"\n✅ ASYNC PROCESSING COMPLETED!")
                    print(f"   Citations found: {len(citations)}")
                    
                    # Check for duplicates
                    citation_texts = [c.get('citation', '').replace('\n', ' ').strip() for c in citations]
                    unique_citations = set(citation_texts)
                    duplicates = len(citation_texts) - len(unique_citations)
                    
                    print(f"   Total citations: {len(citation_texts)}")
                    print(f"   Unique citations: {len(unique_citations)}")
                    print(f"   Duplicates: {duplicates}")
                    
                    if duplicates == 0:
                        print(f"   ✅ ASYNC DEDUPLICATION WORKING!")
                    else:
                        print(f"   ❌ ASYNC DEDUPLICATION FAILED!")
                        from collections import Counter
                        counts = Counter(citation_texts)
                        for citation, count in counts.items():
                            if count > 1:
                                print(f"      '{citation}' appears {count} times")
                    
                    return True
                    
                elif status == 'failed':
                    error = data.get('error', 'Unknown error')
                    print(f"\n❌ ASYNC PROCESSING FAILED: {error}")
                    return False
                    
                else:
                    print(f"   Status: {status} - waiting...")
                    time.sleep(3)
                    
            else:
                print(f"   HTTP {response.status_code} - waiting...")
                time.sleep(3)
                
        except Exception as e:
            print(f"   Error checking status: {e} - waiting...")
            time.sleep(3)
    
    print(f"\n⏰ Timeout after {max_attempts * 3} seconds")
    return False

if __name__ == "__main__":
    check_async_status()
