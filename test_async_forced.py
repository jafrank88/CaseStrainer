#!/usr/bin/env python3
"""
Test async processing with forced mode
"""

import requests
import json
import time

def test_async_forced():
    """Test async processing with force_mode='async'"""
    
    print("Testing async processing with force_mode='async'...")
    
    base_url = "http://localhost:5000/casestrainer/api"
    
    # Text with multiple citations
    text = """
    In Smith v. Jones, 123 U.S. 456 (2023), the court held that precedent.
    This was followed by Brown v. Board of Education, 345 F.2d 789 (2024).
    The appeals court in Davis v. Johnson, 567 S. Ct. 123 (2022), followed this reasoning.
    """
    
    try:
        # Force async mode
        response = requests.post(
            f"{base_url}/analyze",
            data={'text': text, 'type': 'text', 'force_mode': 'async'},
            timeout=10
        )
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'task_id' in data:
                task_id = data['task_id']
                print(f"Task ID: {task_id}")
                print("Task queued for async processing")
                
                # Poll for completion
                max_wait = 120  # 2 minutes
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    status_response = requests.get(
                        f"{base_url}/task_status/{task_id}",
                        timeout=5
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status', 'unknown')
                        progress = status_data.get('progress', 0)
                        
                        print(f"  Status: {status}, Progress: {progress}%")
                        
                        if status == 'completed':
                            # Get final results
                            result_response = requests.get(
                                f"{base_url}/task_result/{task_id}",
                                timeout=5
                            )
                            
                            if result_response.status_code == 200:
                                result_data = result_response.json()
                                citations = result_data.get('citations', [])
                                clusters = result_data.get('clusters', [])
                                
                                print(f"\n✅ Async processing completed!")
                                print(f"Citations found: {len(citations)}")
                                print(f"Clusters found: {len(clusters)}")
                                
                                # Show first few citations
                                for i, c in enumerate(citations[:3]):
                                    print(f"\nCitation {i+1}:")
                                    print(f"  Text: {c.get('citation', 'N/A')}")
                                    print(f"  Case name: {c.get('extracted_case_name', 'N/A')}")
                                    print(f"  Verified: {c.get('verified', False)}")
                            break
                            
                        elif status == 'failed':
                            print(f"❌ Task failed: {status_data.get('error', 'Unknown error')}")
                            break
                            
                        time.sleep(3)
                    else:
                        print(f"Error checking status: {status_response.status_code}")
                        break
                else:
                    print("❌ Timeout waiting for task completion")
            else:
                print("Error: Expected task_id but got immediate response")
                print(f"Response keys: {list(data.keys())}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_async_forced()
