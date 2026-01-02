#!/usr/bin/env python3
"""Test text citation extraction with sync and async modes"""

import requests
import json
import time

def test_text(mode="sync"):
    """Test citation extraction with specified mode"""
    
    # Use a longer text with multiple citations
    test_text = """
    In the case of Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court held that racial segregation in public schools was unconstitutional. 
    This decision was later reinforced in Cooper v. Aaron, 358 U.S. 1 (1958). 
    Another important case is Miranda v. Arizona, 384 U.S. 436 (1966), which established the Miranda warning rights.
    The Court also addressed due process in Gideon v. Wainwright, 372 U.S. 335 (1963).
    More recently, the Court decided Obergefell v. Hodges, 576 U.S. 644 (2015), which legalized same-sex marriage nationwide.
    """
    
    print(f"Testing text citation extraction with {mode} mode...")
    print(f"Text length: {len(test_text)} chars")
    
    # Prepare the request
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    data = {
        "type": "text",
        "text": test_text,
        "force_mode": mode
    }
    
    print(f"Sending request with force_mode={mode}...")
    
    try:
        response = requests.post(url, json=data, timeout=120, verify=False)
        
        print(f"\nStatus code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result:
                task_id = result['task_id']
                print(f"Task ID: {task_id}")
                print("Processing asynchronously...")
                
                # Poll for completion
                max_wait = 60  # 1 minute max
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    try:
                        status_response = requests.get(
                            f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}",
                            timeout=10,
                            verify=False
                        )
                        
                        if status_response.status_code == 200:
                            status = status_response.json()
                            progress = status.get('progress_percent', 0)
                            message = status.get('current_message', '')
                            
                            print(f"Progress: {progress}% - {message}")
                            
                            if status.get('status') == 'completed':
                                print("\n[SUCCESS] Task completed!")
                                return status
                            elif status.get('status') == 'failed':
                                print(f"\n[FAILED] Task failed: {status.get('error', 'Unknown error')}")
                                return status
                        
                        time.sleep(3)  # Wait 3 seconds between checks
                    except Exception as e:
                        print(f"Error checking status: {e}")
                        time.sleep(3)
                
                print("\n[TIMEOUT] Timeout waiting for task completion")
                return None
            else:
                # Synchronous result
                print("Synchronous processing completed")
                
                # Analyze results
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                print(f"\n[SUMMARY] Summary:")
                print(f"   Citations extracted: {len(citations)}")
                print(f"   Clusters formed: {len(clusters)}")
                
                if 'metadata' in result:
                    metadata = result['metadata']
                    print(f"   Processing strategy: {metadata.get('processing_strategy', 'N/A')}")
                    print(f"   Text length: {metadata.get('text_length', 'N/A')}")
                    if 'verified_count' in metadata:
                        print(f"   Verified citations: {metadata['verified_count']}/{len(citations)}")
                
                return result
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:1000])
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

def main():
    """Run both sync and async tests"""
    
    print("Testing text citation extraction with sync and async modes")
    print("="*60)
    
    # Test sync mode
    print("\n1. Testing SYNC mode...")
    sync_result = test_text("sync")
    
    if sync_result:
        print("\n[SUCCESS] Sync mode test completed!")
    else:
        print("\n[FAILED] Sync mode test failed")
    
    # Test async mode
    print("\n\n2. Testing ASYNC mode...")
    async_result = test_text("async")
    
    if async_result:
        print("\n[SUCCESS] Async mode test completed!")
    else:
        print("\n[FAILED] Async mode test failed")
    
    # Compare results
    print("\n\n" + "="*60)
    print("COMPARISON")
    print("="*60)
    
    if sync_result and async_result:
        sync_citations = sync_result.get('citations', [])
        async_result_data = async_result.get('result', {})
        async_citations = async_result_data.get('citations', [])
        
        print(f"Sync citations: {len(sync_citations)}")
        print(f"Async citations: {len(async_citations)}")
        
        if len(sync_citations) == len(async_citations):
            print("[SUCCESS] Citation counts match!")
        else:
            print("[WARNING] Citation counts differ")
        
        # Check if both completed successfully
        sync_status = 'completed' if sync_result else 'failed'
        async_status = async_result.get('status', 'unknown')
        
        if sync_status == 'completed' and async_status == 'completed':
            print("[SUCCESS] Both sync and async completed successfully!")
        else:
            print(f"[WARNING] Status mismatch - Sync: {sync_status}, Async: {async_status}")
    else:
        print("[ERROR] Could not compare - one or both tests failed")

if __name__ == "__main__":
    main()
