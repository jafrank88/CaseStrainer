#!/usr/bin/env python3
"""
Test PDF processing consistency by processing the same PDF twice
"""

import requests
import json
import time
import os

def download_pdf(url, filename):
    """Download PDF from URL"""
    print(f"Downloading PDF from {url}...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with open(filename, 'wb') as f:
        f.write(response.content)
    
    print(f"Downloaded {len(response.content)} bytes to {filename}")
    return filename

def process_pdf(filename):
    """Process a PDF file and return results"""
    
    print(f"\nProcessing {filename}...")
    
    # Submit the request
    api_url = "http://localhost:5000/casestrainer/api/analyze"
    
    # Prepare file upload
    with open(filename, 'rb') as f:
        files = {'file': f}
        data = {
            'type': 'file',
            'enable_verification': 'true'
        }
        
        response = requests.post(api_url, files=files, data=data)
    
    if response.status_code not in [200, 202]:
        print(f"Error: {response.status_code} - {response.text}")
        return None
    
    result = response.json()
    
    # If async, poll for completion
    if result.get("status") == "processing":
        task_id = result["request_id"]
        status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
        
        print(f"Task ID: {task_id}")
        print("Polling for completion...")
        
        poll_count = 0
        while poll_count < 300:  # 10 minutes max
            status_resp = requests.get(status_url)
            if status_resp.status_code == 200:
                status = status_resp.json()
                if status.get("is_finished"):
                    result = status
                    break
                else:
                    poll_count += 1
                    if poll_count % 30 == 0:
                        print(f"  {poll_count*2}s: {status.get('message', 'Processing...')}")
                    time.sleep(2)
            else:
                print(f"Error checking status: {status_resp.status_code}")
                break
    
    return result

def analyze_results(result, run_name):
    """Analyze processing results"""
    if not result:
        return None
    
    citations = result.get("citations", [])
    clusters = result.get("clusters", [])
    metadata = result.get("metadata", {})
    
    # Count Washington citations
    wa_citations = [c for c in citations if "Wn." in c.get("citation", "") or "Wash." in c.get("citation", "")]
    
    # Count verified citations
    verified_count = sum(1 for c in citations if c.get("verified", False))
    
    # Count citations with case names
    with_names = sum(1 for c in citations if c.get("extracted_case_name"))
    
    print(f"\n{run_name} Results:")
    print(f"  Citations: {len(citations)}")
    print(f"  Clusters: {len(clusters)}")
    print(f"  Verified: {verified_count} ({verified_count/len(citations)*100:.1f}%)")
    print(f"  With case names: {with_names} ({with_names/len(citations)*100:.1f}%)")
    print(f"  Washington citations: {len(wa_citations)}")
    print(f"  Document length: {metadata.get('text_length', 0):,} chars")
    print(f"  Processing strategy: {metadata.get('processing_strategy', 'unknown')}")
    
    return {
        "citation_count": len(citations),
        "cluster_count": len(clusters),
        "verified_count": verified_count,
        "verified_rate": verified_count / len(citations) if citations else 0,
        "with_names": with_names,
        "names_rate": with_names / len(citations) if citations else 0,
        "wa_citations": len(wa_citations),
        "document_length": metadata.get('text_length', 0),
        "processing_strategy": metadata.get('processing_strategy'),
        "citations": citations
    }

def compare_runs(run1, run2):
    """Compare two processing runs"""
    print(f"\n{'='*60}")
    print("COMPARISON")
    print(f"{'='*60}")
    
    # Basic metrics
    print(f"\nCitation counts: {run1['citation_count']} vs {run2['citation_count']}")
    print(f"Match: {'✓' if run1['citation_count'] == run2['citation_count'] else '✗'}")
    
    print(f"\nCluster counts: {run1['cluster_count']} vs {run2['cluster_count']}")
    print(f"Match: {'✓' if run1['cluster_count'] == run2['cluster_count'] else '✗'}")
    
    print(f"\nVerification rates: {run1['verified_rate']:.1%} vs {run2['verified_rate']:.1%}")
    print(f"Match: {'✓' if abs(run1['verified_rate'] - run2['verified_rate']) < 0.01 else '✗'}")
    
    print(f"\nCase name rates: {run1['names_rate']:.1%} vs {run2['names_rate']:.1%}")
    print(f"Match: {'✓' if abs(run1['names_rate'] - run2['names_rate']) < 0.01 else '✗'}")
    
    print(f"\nWashington citations: {run1['wa_citations']} vs {run2['wa_citations']}")
    print(f"Match: {'✓' if run1['wa_citations'] == run2['wa_citations'] else '✗'}")
    
    print(f"\nDocument lengths: {run1['document_length']:,} vs {run2['document_length']:,}")
    print(f"Match: {'✓' if run1['document_length'] == run2['document_length'] else '✗'}")
    
    # Check individual citations
    if run1['citation_count'] == run2['citation_count']:
        matches = 0
        print(f"\nChecking first 10 citations:")
        for i in range(min(10, len(run1['citations']))):
            c1 = run1['citations'][i]
            c2 = run2['citations'][i]
            
            if (c1.get('citation') == c2.get('citation') and
                c1.get('extracted_case_name') == c2.get('extracted_case_name') and
                c1.get('verified') == c2.get('verified')):
                matches += 1
                print(f"  {i+1}. ✓ {c1.get('citation')}")
            else:
                print(f"  {i+1}. ✗ {c1.get('citation')} vs {c2.get('citation')}")
        
        print(f"\nCitation match rate: {matches}/{min(10, len(run1['citations']))}")
    
    # Overall conclusion
    all_match = (
        run1['citation_count'] == run2['citation_count'] and
        run1['cluster_count'] == run2['cluster_count'] and
        run1['wa_citations'] == run2['wa_citations'] and
        run1['document_length'] == run2['document_length'] and
        abs(run1['verified_rate'] - run2['verified_rate']) < 0.01
    )
    
    print(f"\nConclusion: {'✓ CONSISTENT' if all_match else '✗ INCONSISTENT'}")

if __name__ == "__main__":
    # Test URL
    url = "https://www.courts.wa.gov/opinions/pdf/402851_pub.pdf"
    filename = "test_consistency.pdf"
    
    print("Testing PDF processing consistency...")
    print(f"URL: {url}")
    
    try:
        # Download PDF
        download_pdf(url, filename)
        
        # Process first time
        print("\n" + "="*60)
        print("RUN 1")
        print("="*60)
        result1 = process_pdf(filename)
        run1 = analyze_results(result1, "Run 1")
        
        # Wait a bit
        print("\nWaiting 5 seconds...")
        time.sleep(5)
        
        # Process second time
        print("\n" + "="*60)
        print("RUN 2")
        print("="*60)
        result2 = process_pdf(filename)
        run2 = analyze_results(result2, "Run 2")
        
        # Compare
        if run1 and run2:
            compare_runs(run1, run2)
    
    finally:
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
            print(f"\nCleaned up {filename}")
