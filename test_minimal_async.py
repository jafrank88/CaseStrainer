#!/usr/bin/env python3
"""
Minimal test to debug async verification issue
"""

import requests
import time

def test_minimal_async():
    """Test minimal async to see debug logs"""
    print("🔧 MINIMAL ASYNC VERIFICATION TEST")
    print("=" * 40)
    
    # Use a simple known verifiable citation repeated to trigger async
    test_text = "The Supreme Court decision in 521 U.S. 811 established important precedent. " * 200
    
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {
        "text": test_text,
        "type": "text"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result:
                task_id = result['task_id']
                print(f"🔄 Task ID: {task_id}")
                
                # Check logs immediately
                print(f"\n📋 Checking worker logs for task {task_id}...")
                
                # Poll for completion
                for attempt in range(30):
                    try:
                        poll_response = requests.get(f"http://localhost:5000/casestrainer/api/task_status/{task_id}")
                        
                        if poll_response.status_code == 200:
                            poll_result = poll_response.json()
                            status = poll_result.get('status', 'unknown')
                            
                            print(f"   Check {attempt+1}: Status = {status}")
                            
                            if status == 'completed':
                                citations = poll_result.get('citations', [])
                                print(f"   ✅ COMPLETED! Found {len(citations)} citations")
                                
                                # Check first few citations for verification
                                verified_count = 0
                                for i, citation in enumerate(citations[:5]):
                                    verified = citation.get('verified', False)
                                    canonical_name = citation.get('canonical_name', None)
                                    print(f"     Citation {i+1}: Verified={verified}, Canonical={canonical_name}")
                                    if verified and canonical_name:
                                        verified_count += 1
                                
                                print(f"\n   📈 Verification Results:")
                                print(f"   Total citations: {len(citations)}")
                                print(f"   Verified with canonical data: {verified_count}")
                                
                                if verified_count > 0:
                                    print(f"   ✅ ASYNC VERIFICATION WORKING!")
                                    return True
                                else:
                                    print(f"   ❌ ASYNC VERIFICATION FAILED")
                                    return False
                                    
                            elif status == 'failed':
                                print(f"   ❌ FAILED: {poll_result.get('error', 'Unknown error')}")
                                return False
                    
                    except Exception as e:
                        print(f"   Check {attempt+1}: Error - {e}")
                    
                    time.sleep(2)
                
                print(f"   ⏰ TIMEOUT")
                return False
            else:
                citations = result.get('result', {}).get('citations', [])
                print(f"📋 Sync response - Found {len(citations)} citations")
                return False
        else:
            print(f"❌ Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    test_minimal_async()
