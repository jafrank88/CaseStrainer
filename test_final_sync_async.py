#!/usr/bin/env python3
"""Final test for sync and async modes with verification"""

import requests
import json
import time

def test_mode(mode="sync", enable_verification=True):
    """Test citation extraction with specified mode and verification"""
    
    # Test with a medium-sized text
    test_text = """
    In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), the United States Supreme Court declared that state laws establishing separate public schools for black and white students were unconstitutional. 
    This decision overturned the Plessy v. Ferguson, 163 U.S. 537 (1896) decision's "separate but equal" doctrine.
    The Court later reinforced this decision in Cooper v. Aaron, 358 U.S. 1 (1958), stating that states must comply with Supreme Court rulings.
    Another important civil rights case is Miranda v. Arizona, 384 U.S. 436 (1966), which established the Miranda warning.
    The Court addressed the right to counsel in Gideon v. Wainwright, 372 U.S. 335 (1963).
    More recently, Obergefell v. Hodges, 576 U.S. 644 (2015) legalized same-sex marriage nationwide.
    """
    
    print(f"\n{'='*60}")
    print(f"Testing {mode.upper()} mode with verification={enable_verification}")
    print(f"{'='*60}")
    print(f"Text length: {len(test_text)} chars")
    
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    data = {
        "type": "text",
        "text": test_text,
        "force_mode": mode,
        "enable_verification": enable_verification
    }
    
    print(f"Sending request with force_mode={mode}, enable_verification={enable_verification}...")
    
    try:
        response = requests.post(url, json=data, timeout=120 if mode == "sync" else 30, verify=False)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result:
                task_id = result['task_id']
                print(f"Task ID: {task_id}")
                print("Processing asynchronously...")
                
                # Poll for completion
                max_wait = 120  # 2 minutes max
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
                
                print(f"\n[RESULTS]")
                print(f"   Citations extracted: {len(citations)}")
                print(f"   Clusters formed: {len(clusters)}")
                
                if 'metadata' in result:
                    metadata = result['metadata']
                    print(f"   Processing strategy: {metadata.get('processing_strategy', 'N/A')}")
                    if 'verified_count' in metadata:
                        print(f"   Verified citations: {metadata['verified_count']}/{len(citations)}")
                
                # Show verification status
                verified_count = sum(1 for c in citations if c.get('verified', False))
                print(f"   Actually verified: {verified_count}/{len(citations)}")
                
                if citations:
                    print(f"\n First 3 citations:")
                    for i, citation in enumerate(citations[:3], 1):
                        print(f"\n{i}. {citation.get('citation', 'N/A')}")
                        print(f"   Case: {citation.get('case_name', 'N/A')[:50]}...")
                        print(f"   Verified: {citation.get('verified', False)}")
                        if citation.get('canonical_name'):
                            print(f"   Canonical: {citation['canonical_name'][:50]}...")
                
                return result
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:1000])
            return None
            
    except requests.exceptions.Timeout:
        print(f"\n[TIMEOUT] {mode.upper()} mode timed out")
        return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def main():
    """Run all test combinations"""
    
    print("Testing sync and async modes with verification enabled/disabled")
    print("="*60)
    
    results = {}
    
    # Test 1: Sync with verification
    results['sync_verified'] = test_mode("sync", True)
    
    # Test 2: Sync without verification
    results['sync_unverified'] = test_mode("sync", False)
    
    # Test 3: Async with verification
    results['async_verified'] = test_mode("async", True)
    
    # Test 4: Async without verification
    results['async_unverified'] = test_mode("async", False)
    
    # Summary
    print("\n\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        mode = test_name.split('_')[0]
        verified = test_name.split('_')[1]
        
        if result:
            if 'result' in result:
                citations = result['result'].get('citations', [])
            else:
                citations = result.get('citations', [])
            
            verified_count = sum(1 for c in citations if c.get('verified', False))
            print(f"{mode.upper()} ({verified}): {len(citations)} citations, {verified_count} verified")
        else:
            print(f"{mode.upper()} ({verified}): FAILED")
    
    print("\n[COMPLETE] All tests finished!")

if __name__ == "__main__":
    main()
