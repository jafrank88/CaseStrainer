#!/usr/bin/env python3
"""
Test script to compare sync vs async processing results
"""

import requests
import json
import time

# Test text with multiple citations
test_text = """
In the landmark case of Brown v. Board of Education, 347 U.S. 483 (1954), the Supreme Court 
held that segregation in public schools was unconstitutional. This decision was followed by 
Brown v. Board of Education II, 349 U.S. 294 (1955), which addressed implementation. 

Earlier, in Plessy v. Ferguson, 163 U.S. 537 (1896), the Court had upheld the "separate but equal" 
doctrine. This was effectively overturned by the Brown decisions.

More recently, in Parents Involved in Community Schools v. Seattle School District No. 1, 
551 U.S. 701 (2007), the Court considered issues of racial integration in schools.
"""

def test_processing(text, force_async=False):
    """Test processing with sync or async"""
    
    # Small text normally processes sync, large text processes async
    # To force async, we'll pad the text to exceed the 5KB threshold
    if force_async:
        padding = "\nThis is padding text to make the document larger. " * 500
        text = padding + text + padding
    
    print(f"\n{'='*60}")
    print(f"Testing {'ASYNC' if force_async else 'SYNC'} processing")
    print(f"Text length: {len(text)} characters")
    print(f"{'='*60}")
    
    # Submit the request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": text}
    
    start_time = time.time()
    response = requests.post(url, json=data)
    elapsed = time.time() - start_time
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    
    result = response.json()
    
    # For async processing, we need to poll for the actual results
    # The initial response just contains the task_id
    if result.get("status") == "processing":
        print(f"Async processing initiated, request_id: {result['request_id']}")
        
        # Poll for completion
        task_id = result["request_id"]
        status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
        
        poll_count = 0
        max_polls = 60  # Maximum 2 minutes
        
        while poll_count < max_polls:
            status_resp = requests.get(status_url)
            if status_resp.status_code == 200:
                status = status_resp.json()
                if status.get("is_finished"):
                    result = status
                    break
                else:
                    poll_count += 1
                    if poll_count % 10 == 0:  # Only print every 10 seconds
                        print(f"  Progress: {status.get('message', 'Processing...')} ({poll_count*2}s)")
                    time.sleep(2)
            else:
                print(f"Error checking status: {status_resp.status_code}")
                break
        
        if not result.get("is_finished"):
            print(f"Warning: Async task did not complete within {max_polls*2} seconds")
            return None
    
    # Analyze results
    citations = result.get("citations", [])
    clusters = result.get("clusters", [])
    
    print(f"\nResults:")
    print(f"  Processing time: {elapsed:.2f}s")
    print(f"  Total citations: {len(citations)}")
    print(f"  Total clusters: {len(clusters)}")
    print(f"  Processing mode: {result.get('metadata', {}).get('processing_strategy', 'unknown')}")
    
    # Check case name extraction
    extracted_names = [c.get("extracted_case_name") for c in citations if c.get("extracted_case_name")]
    verified_count = sum(1 for c in citations if c.get("verified", False))
    
    print(f"\nCase Name Extraction:")
    print(f"  Citations with case names: {len(extracted_names)}/{len(citations)}")
    print(f"  Verified citations: {verified_count}/{len(citations)}")
    
    # Show first few citations
    print(f"\nFirst 3 citations:")
    for i, cit in enumerate(citations[:3]):
        print(f"  {i+1}. {cit.get('citation', 'Unknown')}")
        print(f"     Extracted: {cit.get('extracted_case_name', 'None')}")
        print(f"     Canonical: {cit.get('canonical_name', 'None')}")
        print(f"     Verified: {cit.get('verified', False)}")
    
    # Check for differences
    return {
        "citations": citations,
        "clusters": clusters,
        "processing_mode": result.get('metadata', {}).get('processing_strategy'),
        "extraction_rate": len(extracted_names) / len(citations) if citations else 0,
        "verification_rate": verified_count / len(citations) if citations else 0,
        "processing_time": elapsed
    }

def compare_results(sync_result, async_result):
    """Compare sync and async results"""
    
    print(f"\n{'='*60}")
    print("COMPARISON")
    print(f"{'='*60}")
    
    sync_cits = sync_result["citations"]
    async_cits = async_result["citations"]
    
    # Basic metrics
    print(f"\nBasic Metrics:")
    print(f"  Sync citations: {len(sync_cits)}")
    print(f"  Async citations: {len(async_cits)}")
    print(f"  Citation count match: {len(sync_cits) == len(async_cits)}")
    
    # Extraction quality
    print(f"\nExtraction Quality:")
    print(f"  Sync extraction rate: {sync_result['extraction_rate']:.1%}")
    print(f"  Async extraction rate: {async_result['extraction_rate']:.1%}")
    print(f"  Sync verification rate: {sync_result['verification_rate']:.1%}")
    print(f"  Async verification rate: {async_result['verification_rate']:.1%}")
    
    # Check if citations match
    if len(sync_cits) == len(async_cits):
        matches = 0
        for sync_cit, async_cit in zip(sync_cits, async_cits):
            if (sync_cit.get("citation") == async_cit.get("citation") and
                sync_cit.get("extracted_case_name") == async_cit.get("extracted_case_name")):
                matches += 1
        
        print(f"\nCitation Match Analysis:")
        print(f"  Exact matches: {matches}/{len(sync_cits)} ({matches/len(sync_cits):.1%})")
    
    # Processing time
    print(f"\nPerformance:")
    print(f"  Sync time: {sync_result['processing_time']:.2f}s")
    print(f"  Async time: {async_result['processing_time']:.2f}s")
    
    # Conclusion
    print(f"\nConclusion:")
    if (len(sync_cits) == len(async_cits) and
        abs(sync_result['extraction_rate'] - async_result['extraction_rate']) < 0.1 and
        abs(sync_result['verification_rate'] - async_result['verification_rate']) < 0.1):
        print("  ✓ Sync and Async produce CONSISTENT results")
    else:
        print("  ✗ Sync and Async produce DIFFERENT results")

if __name__ == "__main__":
    print("Testing sync vs async processing consistency...")
    
    # Test sync (small text)
    sync_result = test_processing(test_text, force_async=False)
    
    # Test async (large text)
    async_result = test_processing(test_text, force_async=True)
    
    # Compare
    if sync_result and async_result:
        compare_results(sync_result, async_result)
