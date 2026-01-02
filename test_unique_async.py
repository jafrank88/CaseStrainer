#!/usr/bin/env python3
"""
Test async processing with unique citations
"""

import requests
import time

def test_unique_async():
    """Test async processing with unique citations"""
    
    print("TESTING ASYNC WITH UNIQUE CITATIONS")
    print("=" * 40)
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Create text with unique citations (no repeats)
    text = """
    In the case of Smith v. Jones, 123 U.S. 456 (2023), the court held that...
    Additionally, in Brown v. Board, 345 F.2d 789 (2024), we find that...
    The precedent in Davis v. Johnson, 567 S. Ct. 123 (2022) suggests...
    """
    
    # Make it large enough to trigger async
    text = text * 100
    
    print(f"\n1. Submitting text ({len(text)} chars)...")
    try:
        response = requests.post(
            f"{base_url}/analyze",
            data={'text': text, 'type': 'text'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'task_id' in result:
                task_id = result['task_id']
                print(f"   OK Got task_id: {task_id}")
                
                # Check if it's in Redis
                check_cmd = f'docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** exists "rq:job:{task_id}"'
                import subprocess
                result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
                if result.stdout.strip() == '1':
                    print("   Task exists in Redis")
                    
                    # Check status
                    status_cmd = f'docker exec casestrainer-redis-prod redis-cli -a ***REDACTED_REDIS_PASSWORD*** hget "rq:job:{task_id}" status'
                    result = subprocess.run(status_cmd, shell=True, capture_output=True, text=True)
                    print(f"   Initial status: {result.stdout.strip()}")
                else:
                    print("   Task NOT found in Redis")
            else:
                print("   Got immediate response")
        else:
            print(f"   Error: {response.status_code}")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_unique_async()
