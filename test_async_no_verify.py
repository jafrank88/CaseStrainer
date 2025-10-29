#!/usr/bin/env python
"""Test async processing with verification disabled."""

import requests
import time

# Text large enough for async processing
test_text = """
In Smith v. Jones, 123 U.S. 456 (2020), the court established precedent.
In Johnson v. Smith, 456 F.2d 789 (2021), the Ninth Circuit addressed digital contracts.
The landmark Brown v. Board of Education, 347 U.S. 483 (1954), ended segregation.
In Roe v. Wade, 410 U.S. 113 (1973), the Court recognized privacy rights.
Miranda v. Arizona, 384 U.S. 436 (1966) established warnings.
""" * 25  # Repeat to exceed 5KB

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
data = {
    "text": test_text,
    "enable_verification": False,  # Disable verification
    "client_request_id": f"test_async_no_verify_{int(time.time())}"
}

print("=" * 60)
print("TESTING ASYNC PROCESSING WITHOUT VERIFICATION")
print("=" * 60)
print(f"Text length: {len(test_text)} chars (> 5KB for async)")
print(f"enable_verification: False")

try:
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
    result = response.json()
    
    print(f"\n✅ Submitted successfully!")
    print(f"Status: {result.get('status')}")
    print(f"Processing mode: {result.get('metadata', {}).get('processing_mode')}")
    
    task_id = result.get('task_id')
    if task_id:
        print(f"Task ID: {task_id}")
        
        # Monitor progress
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        
        start_time = time.time()
        while time.time() - start_time < 30:  # 30 second timeout
            try:
                status_response = requests.get(status_url, timeout=5)
                status = status_response.json()
                
                progress = status.get('verification_status', {}).get('progress_percent', 0)
                message = status.get('verification_status', {}).get('current_message', '')
                
                if progress > 0:
                    print(f"  Progress: {progress}% - {message}")
                
                if status.get('status') == 'completed':
                    elapsed = time.time() - start_time
                    print(f"\n✅ COMPLETED in {elapsed:.1f} seconds!")
                    
                    if 'result' in status:
                        result = status['result']
                        citations = result.get('citations', [])
                        clusters = result.get('clusters', [])
                        
                        print(f"\n📊 Results:")
                        print(f"Citations: {len(citations)}")
                        print(f"Clusters: {len(clusters)}")
                        
                        # Check if verification was skipped
                        verified = sum(1 for c in citations if c.get('verified'))
                        print(f"Verified citations: {verified}")
                        
                        if verified == 0 and elapsed < 10:
                            print("\n✅ VERIFICATION SUCCESSFULLY SKIPPED!")
                            print("✅ Processing completed quickly without verification delays")
                            print("✅ FIX CONFIRMED: enable_verification=False is working!")
                        else:
                            print(f"\n⚠️  Verification may have run")
                            print(f"  Time: {elapsed:.1f}s, Verified: {verified}")
                        
                        # Show sample citations
                        print(f"\n📋 Sample citations:")
                        for i, cit in enumerate(citations[:5]):
                            print(f"  {i+1}. {cit.get('citation', 'N/A')}")
                    break
                elif status.get('status') == 'failed':
                    error = status.get('error', 'Unknown error')
                    print(f"\n❌ Failed: {error}")
                    break
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(1)
        else:
            print(f"\n⏰ Timeout after 30 seconds")
            print("If verification was running, it would take much longer")
    else:
        print(f"❌ Processed synchronously (unexpected for >5KB)")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
