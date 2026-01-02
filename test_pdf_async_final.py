#!/usr/bin/env python3
"""Test PDF citation extraction with async mode"""

import requests
import json
import time

def test_pdf_async():
    """Test citation extraction from PDF with async mode"""
    
    pdf_path = r"D:\dev\casestrainer\23SC959.pdf"
    
    # Read the PDF file
    try:
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
    except FileNotFoundError:
        print(f"ERROR: PDF file not found at {pdf_path}")
        return None
    except Exception as e:
        print(f"ERROR: Could not read PDF file: {e}")
        return None
    
    print(f"Testing PDF citation extraction with async mode...")
    print(f"PDF size: {len(pdf_content)} bytes")
    
    # Prepare the request
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    files = {
        'file': ('23SCSC959.pdf', pdf_content, 'application/pdf')
    }
    
    data = {
        'force_mode': 'async'
    }
    
    print(f"Sending request with force_mode=async...")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=60, verify=False)
        
        print(f"\nStatus code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'task_id' in result:
                task_id = result['task_id']
                print(f"Task ID: {task_id}")
                print("Processing asynchronously...")
                
                # Poll for completion
                max_wait = 300  # 5 minutes max
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
                        
                        time.sleep(5)  # Wait 5 seconds between checks
                    except Exception as e:
                        print(f"Error checking status: {e}")
                        time.sleep(5)
                
                print("\n[TIMEOUT] Timeout waiting for task completion")
                return None
            else:
                print("ERROR: No task_id returned for async mode")
                return result
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:1000])
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

def analyze_results(result):
    """Analyze and print results"""
    
    if not result:
        print("\n[ERROR] No results to analyze")
        return
    
    print("\n" + "="*60)
    print("PDF ASYNC MODE RESULTS")
    print("="*60)
    
    # Extract citations and clusters
    if 'result' in result:
        citations = result['result'].get('citations', [])
        clusters = result['result'].get('clusters', [])
    else:
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
    
    # Show first few citations
    if citations:
        print(f"\n[CITATIONS] First 5 citations:")
        for i, citation in enumerate(citations[:5], 1):
            print(f"\n{i}. {citation.get('citation', 'N/A')}")
            print(f"   Case: {citation.get('case_name', 'N/A')}")
            print(f"   Verified: {citation.get('verified', False)}")
            if citation.get('canonical_name'):
                print(f"   Canonical: {citation['canonical_name']}")
    
    # Show clusters
    if clusters:
        print(f"\n[CLUSTERS] First 3 clusters:")
        for i, cluster in enumerate(clusters[:3], 1):
            cluster_size = cluster.get('cluster_size', 0)
            cluster_case = cluster.get('cluster_case_name', 'N/A')
            print(f"\n{i}. Cluster: {cluster_case} ({cluster_size} citations)")
            if cluster.get('canonical_name'):
                print(f"   Canonical: {cluster['canonical_name']}")
    
    print(f"\n[SUCCESS] PDF async mode test completed successfully!")

if __name__ == "__main__":
    result = test_pdf_async()
    analyze_results(result)
