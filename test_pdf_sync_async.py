#!/usr/bin/env python3
"""
Test sync vs async processing with a PDF URL
"""

import requests
import json
import time

def test_url_processing(url, force_async=False):
    """Test processing a URL"""
    
    print(f"\n{'='*60}")
    print(f"Testing {'ASYNC' if force_async else 'SYNC'} processing")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    # Submit the request
    api_url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"url": url}
    
    start_time = time.time()
    response = requests.post(api_url, json=data)
    elapsed = time.time() - start_time
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    
    result = response.json()
    
    # For async processing, we need to poll for the actual results
    if result.get("status") == "processing":
        print(f"Async processing initiated, request_id: {result['request_id']}")
        
        # Poll for completion
        task_id = result["request_id"]
        status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
        
        poll_count = 0
        max_polls = 300  # Maximum 10 minutes for large PDFs
        
        while poll_count < max_polls:
            status_resp = requests.get(status_url)
            if status_resp.status_code == 200:
                status = status_resp.json()
                if status.get("is_finished"):
                    result = status
                    break
                else:
                    poll_count += 1
                    if poll_count % 30 == 0:  # Print every minute
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
    metadata = result.get("metadata", {})
    
    print(f"\nResults:")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Processing time: {metadata.get('processing_time_ms', 0)/1000:.2f}s")
    print(f"  Total citations: {len(citations)}")
    print(f"  Total clusters: {len(clusters)}")
    print(f"  Processing mode: {metadata.get('processing_strategy', 'unknown')}")
    print(f"  Document length: {metadata.get('text_length', 0)} characters")
    
    # Check case name extraction
    extracted_names = [c.get("extracted_case_name") for c in citations if c.get("extracted_case_name")]
    verified_count = sum(1 for c in citations if c.get("verified", False))
    
    print(f"\nCase Name Extraction:")
    print(f"  Citations with case names: {len(extracted_names)}/{len(citations)} ({len(extracted_names)/len(citations)*100:.1f}%)")
    print(f"  Verified citations: {verified_count}/{len(citations)} ({verified_count/len(citations)*100:.1f}%)")
    
    # Show first few citations
    print(f"\nFirst 5 citations:")
    for i, cit in enumerate(citations[:5]):
        print(f"  {i+1}. {cit.get('citation', 'Unknown')}")
        print(f"     Extracted: {cit.get('extracted_case_name', 'None')[:50]}{'...' if len(cit.get('extracted_case_name', '')) > 50 else ''}")
        print(f"     Canonical: {cit.get('canonical_name', 'None')[:50]}{'...' if len(cit.get('canonical_name', '')) > 50 else ''}")
        print(f"     Verified: {cit.get('verified', False)}")
    
    # Check for Washington citations
    wa_citations = [c for c in citations if "Wn." in c.get("citation", "") or "Wash." in c.get("citation", "")]
    print(f"\nWashington citations: {len(wa_citations)}")
    
    return {
        "citations": citations,
        "clusters": clusters,
        "processing_mode": metadata.get('processing_strategy'),
        "extraction_rate": len(extracted_names) / len(citations) if citations else 0,
        "verification_rate": verified_count / len(citations) if citations else 0,
        "total_time": elapsed,
        "processing_time": metadata.get('processing_time_ms', 0)/1000,
        "document_length": metadata.get('text_length', 0)
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
    print(f"  Citation count match: {'✓' if len(sync_cits) == len(async_cits) else '✗'}")
    
    # Document processing
    print(f"\nDocument Processing:")
    print(f"  Sync document length: {sync_result['document_length']:,} chars")
    print(f"  Async document length: {async_result['document_length']:,} chars")
    print(f"  Document length match: {'✓' if sync_result['document_length'] == async_result['document_length'] else '✗'}")
    
    # Extraction quality
    print(f"\nExtraction Quality:")
    print(f"  Sync extraction rate: {sync_result['extraction_rate']:.1%}")
    print(f"  Async extraction rate: {async_result['extraction_rate']:.1%}")
    print(f"  Sync verification rate: {sync_result['verification_rate']:.1%}")
    print(f"  Async verification rate: {async_result['verification_rate']:.1%}")
    
    # Performance
    print(f"\nPerformance:")
    print(f"  Sync total time: {sync_result['total_time']:.2f}s")
    print(f"  Async total time: {async_result['total_time']:.2f}s")
    print(f"  Sync processing time: {sync_result['processing_time']:.2f}s")
    print(f"  Async processing time: {async_result['processing_time']:.2f}s")
    
    # Check if citations match
    if len(sync_cits) == len(async_cits):
        matches = 0
        for sync_cit, async_cit in zip(sync_cits, async_cits):
            if (sync_cit.get("citation") == async_cit.get("citation") and
                sync_cit.get("extracted_case_name") == async_cit.get("extracted_case_name")):
                matches += 1
        
        print(f"\nCitation Match Analysis:")
        print(f"  Exact matches: {matches}/{len(sync_cits)} ({matches/len(sync_cits):.1%})")
    
    # Conclusion
    print(f"\nConclusion:")
    if (len(sync_cits) == len(async_cits) and
        sync_result['document_length'] == async_result['document_length'] and
        abs(sync_result['extraction_rate'] - async_result['extraction_rate']) < 0.05 and
        abs(sync_result['verification_rate'] - async_result['verification_rate']) < 0.05):
        print("  ✓ Sync and Async produce CONSISTENT results")
    else:
        print("  ✗ Sync and Async produce DIFFERENT results")

if __name__ == "__main__":
    # Test URL
    url = "https://www.courts.wa.gov/opinions/pdf/402851_pub.pdf"
    
    print("Testing sync vs async processing with PDF URL...")
    print(f"URL: {url}")
    
    # First, let's check if the URL is accessible
    print("\nChecking URL accessibility...")
    try:
        response = requests.head(url, timeout=10)
        print(f"URL status: {response.status_code}")
        print(f"Content type: {response.headers.get('content-type', 'unknown')}")
        print(f"Content length: {response.headers.get('content-length', 'unknown')} bytes")
    except Exception as e:
        print(f"Error accessing URL: {e}")
        exit(1)
    
    # Test sync (PDFs normally process async, but we'll check what happens)
    print("\n" + "="*60)
    print("NOTE: PDFs typically always process asynchronously due to size")
    print("="*60)
    
    sync_result = test_url_processing(url, force_async=False)
    
    # Wait a bit before testing again
    print("\nWaiting 5 seconds before second test...")
    time.sleep(5)
    
    # Test async
    async_result = test_url_processing(url, force_async=True)
    
    # Compare
    if sync_result and async_result:
        compare_results(sync_result, async_result)
