#!/usr/bin/env python
"""Test that enable_verification=False is now respected."""

import requests
import time

# Simple text to test quickly
test_text = """
In Smith v. Jones, 123 U.S. 456 (2020), the court established precedent.
In Johnson v. Smith, 456 F.2d 789 (2021), the Ninth Circuit addressed digital contracts.
The landmark Brown v. Board of Education, 347 U.S. 483 (1954), ended segregation.
""" * 25  # Repeat to exceed 5KB threshold

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
data = {
    "text": test_text,
    "enable_verification": False,  # Explicitly disable verification
    "client_request_id": f"test_flag_{int(time.time())}"
}

print("=" * 60)
print("TESTING VERIFICATION FLAG FIX")
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
        while time.time() - start_time < 15:  # 15 second timeout
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
                        
                        # Check if verification was actually skipped
                        verified = sum(1 for c in citations if c.get('verified'))
                        print(f"Verified citations: {verified}")
                        
                        if verified == 0 and elapsed < 10:
                            print("✅ VERIFICATION SUCCESSFULLY SKIPPED!")
                            print("✅ Processing completed quickly without verification delays")
                        else:
                            print(f"⚠️  Verification may have run (took {elapsed:.1f}s, {verified} verified)")
                        
                        print(f"\n🎉 FIX VALIDATION COMPLETE")
                    break
                elif status.get('status') == 'failed':
                    print(f"\n❌ Failed: {status.get('error', 'Unknown error')}")
                    break
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(1)
        else:
            print(f"\n⏰ Timeout after 15 seconds")
            print("If verification was running, it would take much longer")
    else:
        print(f"❌ Processed synchronously (unexpected for >5KB)")
        
except Exception as e:
    print(f"❌ Error: {e}")
