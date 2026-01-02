#!/usr/bin/env python3
"""
Test async processing with URL to trigger async mode
"""

import requests
import time

def test_url_async():
    """Test async processing with a URL"""
    
    print("TESTING ASYNC PROCESSING WITH URL")
    print("=" * 40)
    
    base_url = "https://wolf.law.uw.edu/casestrainer"
    
    # Use a known legal document URL
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    print(f"\n1. Testing URL: {test_url}")
    
    try:
        # Submit URL for processing
        response = requests.post(
            f"{base_url}/api/analyze",
            data={'url': test_url, 'type': 'url'},
            timeout=30
        )
        
        print(f"   Submit status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Response type: {'Immediate' if 'citations' in result else 'Async'}")
            
            if 'task_id' in result:
                # Async processing
                task_id = result['task_id']
                print(f"   Task ID: {task_id}")
                
                # Monitor task status
                print("\n2. Monitoring task status...")
                unknown_count = 0
                status_history = []
                
                for i in range(60):  # Check for 2 minutes
                    status_response = requests.get(
                        f"{base_url}/api/task_status/{task_id}",
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        progress = status_data.get('progress', 0)
                        error = status_data.get('error')
                        
                        status_history.append((i+1, status, progress))
                        print(f"   Check {i+1:2d}: Status={status:12s} Progress={progress:3d}%")
                        
                        if status == 'completed':
                            print("   SUCCESS: Task completed!")
                            result = status_data.get('result', {})
                            citations = result.get('citations', [])
                            clusters = result.get('clusters', [])
                            print(f"   Results: {len(citations)} citations, {len(clusters)} clusters")
                            break
                        elif status == 'failed':
                            print(f"   ERROR: Task failed - {error}")
                            break
                        elif status == 'unknown':
                            unknown_count += 1
                            if unknown_count == 1:
                                print("   WARNING: First 'unknown' status detected")
                                print("   This indicates the task status cannot be determined")
                            elif unknown_count > 3:
                                print("   ERROR: Multiple 'unknown' statuses - task is lost")
                                print("   This is the issue you're experiencing!")
                                break
                        elif status == 'queued':
                            print("   INFO: Task is queued waiting for worker")
                        elif status == 'started':
                            print("   INFO: Task is being processed")
                        
                        time.sleep(2)
                    else:
                        print(f"   ERROR: Status check failed - {status_response.status_code}")
                        break
                else:
                    print("   TIMEOUT: Task did not complete in 2 minutes")
                    print(f"   Final unknown count: {unknown_count}")
                    
                    # Analyze status pattern
                    if unknown_count > 0:
                        print("\n   STATUS PATTERN ANALYSIS:")
                        recent_statuses = status_history[-10:]
                        unknown_recent = sum(1 for _, s, _ in recent_statuses if s == 'unknown')
                        if unknown_recent >= 5:
                            print("   DIAGNOSIS: Task is stuck in 'unknown' status")
                            print("   CAUSE: Worker communication issue or task lost")
            
            elif 'citations' in result:
                print("   Immediate processing (unexpected for URL)")
            
        else:
            print(f"   ERROR: Submit failed - {response.text}")
    
    except Exception as e:
        print(f"   ERROR: {e}")
    
    print("\nSOLUTIONS FOR 'UNKNOWN' STATUS:")
    print("1. Restart workers: ./cslaunch")
    print("2. Clear stuck jobs: python clear_stuck_jobs.py")
    print("3. Check Redis connection: python check_redis_auth.py")
    print("4. Monitor worker logs: docker-compose logs rqworker")

if __name__ == "__main__":
    test_url_async()
