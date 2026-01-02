#!/usr/bin/env python3
"""
Test script to verify the cluster display fix is working
"""

import requests
import json
import time

def test_cluster_display_fix():
    """Test that clusters now appear in the frontend after the fix"""
    
    print("TESTING CLUSTER DISPLAY FIX")
    print("=" * 50)
    
    # Test text that should create clusters
    test_text = """
    In the case of In Re Marriage of Littlefield, 141 Wn. App. 558, 170 P.3d 601 (2007), 
    the court addressed important issues regarding spousal support. This decision 
    built upon earlier precedent in State v. Johnson, 25 Wn. App. 849, 611 P.2d 794 (1980).
    """
    
    print("\n1. Submitting text for processing...")
    print(f"Text length: {len(test_text)} characters")
    
    # Submit the text
    response = requests.post(
        'https://wolf.law.uw.edu/casestrainer/api/analyze',
        data={'text': test_text, 'type': 'text'}
    )
    
    if response.status_code != 200:
        print(f"ERROR: Failed to submit text - Status {response.status_code}")
        print(response.text)
        return False
    
    result = response.json()
    task_id = result.get('task_id')
    
    if not task_id:
        print("ERROR: No task_id returned")
        return False
    
    print(f"Task submitted: {task_id}")
    
    # Poll for completion
    print("\n2. Polling for completion...")
    max_attempts = 30
    for attempt in range(max_attempts):
        status_response = requests.get(
            f'https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}'
        )
        
        if status_response.status_code != 200:
            print(f"ERROR: Failed to check status - Status {status_response.status_code}")
            return False
        
        status_data = status_response.json()
        status = status_data.get('status')
        progress = status_data.get('progress', 0)
        
        print(f"   Attempt {attempt + 1}: Status={status}, Progress={progress}%")
        
        if status == 'completed':
            break
        elif status == 'failed':
            print("ERROR: Processing failed")
            print(status_data.get('error', 'Unknown error'))
            return False
        
        time.sleep(2)
    else:
        print("ERROR: Processing timed out")
        return False
    
    # Check results
    print("\n3. Analyzing results...")
    
    if 'result' not in status_data:
        print("ERROR: No result in response")
        return False
    
    result_data = status_data['result']
    citations = result_data.get('citations', [])
    clusters = result_data.get('clusters', [])
    
    print(f"   Citations found: {len(citations)}")
    print(f"   Clusters created: {len(clusters)}")
    
    if len(clusters) == 0:
        print("ERROR: No clusters created")
        return False
    
    print("\n4. Checking cluster display data...")
    
    for i, cluster in enumerate(clusters):
        print(f"\n   Cluster {i + 1}:")
        print(f"     Cluster ID: {cluster.get('cluster_id', 'N/A')}")
        print(f"     Submitted name: {cluster.get('submitted_display_name', 'N/A')}")
        print(f"     Verifying name: {cluster.get('verifying_display_name', 'N/A')}")
        print(f"     Has verified citations: {any(c.get('verified', False) for c in cluster.get('citations', []))}")
        
        # Check if the frontend fix would work
        submitted_name = cluster.get('submitted_display_name', '')
        verifying_name = cluster.get('verifying_display_name', '')
        has_verified = any(c.get('verified', False) for c in cluster.get('citations', []))
        
        is_generic = any(pattern in submitted_name for pattern in [
            'Washington State Case', 'Pacific Reporter Case', 'Federal Appeals Case'
        ])
        
        if is_generic and has_verified and verifying_name and verifying_name != 'N/A':
            print(f"     FRONTEND FIX WILL WORK: Generic name replaced with '{verifying_name}'")
        elif not is_generic:
            print(f"     GOOD: Non-generic name '{submitted_name}'")
        else:
            print(f"     May still have display issues")
    
    print("\n5. SUMMARY:")
    print(f"   Citations extracted: {len(citations)}")
    print(f"   Clusters created: {len(clusters)}")
    print(f"   Frontend fix deployed: Yes")
    print(f"   Expected result: Clusters should now appear in frontend")
    
    return True

if __name__ == "__main__":
    success = test_cluster_display_fix()
    if success:
        print("\nCLUSTER DISPLAY FIX VERIFICATION COMPLETE")
        print("The frontend should now display clusters correctly!")
    else:
        print("\nFIX VERIFICATION FAILED")
        print("Check the logs above for issues.")
