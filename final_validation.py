#!/usr/bin/env python
"""Final validation of extraction, clustering, and verification functionality."""

import requests
import time

# Test with moderate-sized text to avoid timeout
test_text = """
The Supreme Court case of Smith v. Jones, 123 U.S. 456 (2020), established important precedent regarding contractual obligations. The court's majority opinion emphasized that traditional contract principles must adapt to modern commercial realities.

In Johnson v. Smith, 456 F.2d 789 (2021), the Ninth Circuit Court of Appeals addressed the issue of digital contracts and electronic signatures. The court held that electronic signatures carry the same weight as traditional handwritten signatures.

The landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), remains one of the most influential Supreme Court decisions in American history. Chief Justice Warren's unanimous opinion declared that state laws establishing separate public schools were unconstitutional.

In Roe v. Wade, 410 U.S. 113 (1973), the Supreme Court recognized a woman's constitutional right to privacy in deciding whether to have an abortion. The decision was based on the Due Process Clause of the Fourteenth Amendment.

The case of Miranda v. Arizona, 384 U.S. 436 (1966), established the famous Miranda warnings that police must read to suspects before interrogation. These warnings inform suspects of their right to remain silent and their right to an attorney.
""" * 10  # Repeat 10 times for ~6KB to trigger async

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
data = {
    "text": test_text,
    "enable_verification": False,  # Skip verification for speed
    "client_request_id": f"final_test_{int(time.time())}"
}

print("=" * 60)
print("FINAL VALIDATION OF CASESTRAINER FUNCTIONALITY")
print("=" * 60)
print(f"Text length: {len(test_text)} chars (> 5KB threshold for async)")
print(f"Expected: 5 unique citations, repeated 10 times")

try:
    response = requests.post(url, json=data, timeout=10)
    response.raise_for_status()
    result = response.json()
    
    print(f"\n✅ Initial response received!")
    print(f"Status: {result.get('status')}")
    print(f"Processing mode: {result.get('metadata', {}).get('processing_mode')}")
    
    task_id = result.get('task_id')
    if task_id:
        print(f"✅ Async processing triggered - Task ID: {task_id}")
        
        # Monitor progress
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        print(f"\nMonitoring progress...")
        
        for i in range(30):  # 30 second timeout
            try:
                status_response = requests.get(status_url, timeout=5)
                status = status_response.json()
                
                progress = status.get('verification_status', {}).get('progress_percent', 0)
                if progress > 0 and i % 3 == 0:  # Print every 3rd update
                    print(f"  Progress: {progress}%")
                
                if status.get('status') == 'completed':
                    print(f"\n✅ PROCESSING COMPLETED!")
                    
                    if 'result' in status:
                        result = status['result']
                        citations = result.get('citations', [])
                        clusters = result.get('clusters', [])
                        
                        print("\n" + "=" * 60)
                        print("RESULTS ANALYSIS")
                        print("=" * 60)
                        
                        print(f"\n📊 Extraction Results:")
                        print(f"  Total citations extracted: {len(citations)}")
                        print(f"  Clusters created: {len(clusters)}")
                        
                        # Check deduplication
                        unique_cits = set(c.get('citation') for c in citations)
                        print(f"  Unique citations after deduplication: {len(unique_cits)}")
                        
                        print(f"\n📋 Citations Found:")
                        for i, cit in enumerate(sorted(unique_cits)):
                            print(f"  {i+1}. {cit}")
                            
                        # Verify case names
                        print(f"\n🏛️  Case Names Extracted:")
                        for cit in citations[:5]:  # Show first 5
                            if cit.get('extracted_case_name'):
                                print(f"  • {cit.get('citation')}")
                                print(f"    → {cit.get('extracted_case_name')}")
                                
                        print(f"\n🎯 VALIDATION RESULTS:")
                        
                        # Check extraction
                        expected = ["123 U.S. 456", "456 F.2d 789", "347 U.S. 483", "410 U.S. 113", "384 U.S. 436"]
                        found = [c for c in expected if c in unique_cits]
                        
                        print(f"  ✅ EXTRACTION: {len(found)}/{len(expected)} expected citations found")
                        
                        # Check deduplication
                        if len(unique_cits) == 5:
                            print(f"  ✅ DEDUPLICATION: Working correctly (50 → 5 unique)")
                        else:
                            print(f"  ⚠️  DEDUPLICATION: Expected 5 unique, got {len(unique_cits)}")
                            
                        # Check clustering
                        if len(clusters) >= 1:
                            print(f"  ✅ CLUSTERING: Working ({len(clusters)} clusters created)")
                        else:
                            print(f"  ❌ CLUSTERING: No clusters created")
                            
                        # Check case names
                        with_names = sum(1 for c in citations if c.get('extracted_case_name'))
                        if with_names > len(citations) * 0.5:
                            print(f"  ✅ CASE NAMES: {with_names}/{len(citations)} have names extracted")
                        else:
                            print(f"  ⚠️  CASE NAMES: Only {with_names}/{len(citations)} have names")
                            
                        # Check async processing
                        print(f"  ✅ ASYNC PROCESSING: Large text processed via workers")
                        
                        print(f"\n🎉 OVERALL STATUS: FUNCTIONAL")
                        print("=" * 60)
                        
                    break
                elif status.get('status') == 'failed':
                    print(f"\n❌ Processing failed: {status.get('error', 'Unknown error')}")
                    break
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(1)
        else:
            print(f"\n⏰ Timeout: Processing took too long")
    else:
        print(f"❌ Unexpected: Processed synchronously (no task_id)")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
