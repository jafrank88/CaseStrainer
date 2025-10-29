#!/usr/bin/env python
"""Test script to check if extraction, clustering, and verification are working with a real PDF."""

import sys
import os
import requests
import json
import time

def test_pdf_processing():
    """Test if extraction, clustering, and verification are working with a PDF."""
    
    print("Testing extraction, clustering, and verification with PDF...")
    
    # Test PDF path - using a real PDF from root directory
    file_path = "d:\\dev\\casestrainer\\1028814.pdf"
    
    # Submit job
    url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    files = {'file': open(file_path, 'rb')}
    data = {
        "enable_verification": True,
        "client_request_id": f"test_pdf_{int(time.time())}"
    }
    
    print(f"Submitting PDF upload with ID: {data['client_request_id']}")
    print(f"File size: {os.path.getsize(file_path):,} bytes")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        print(f"Response from analyze endpoint: {result}")
        
        task_id = result.get('task_id')
        print(f"Job submitted with task_id: {task_id}")
        
        if not task_id:
            print("ERROR: No task_id in response!")
            print("This might mean the file was processed synchronously")
            return
        
        # Poll for progress
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        
        last_progress = 0
        progress_updates = []
        
        for i in range(300):  # Check for up to 5 minutes for PDF processing
            try:
                status_response = requests.get(status_url, timeout=5)
                status_response.raise_for_status()
                status = status_response.json()
                
                # Check verification status for progress
                if 'verification_status' in status:
                    ver_status = status['verification_status']
                    if isinstance(ver_status, dict):
                        progress = ver_status.get('progress_percent', 0)
                        message = ver_status.get('current_message', '')
                        
                        if progress != last_progress:
                            progress_updates.append((progress, message))
                            print(f"Progress update: {progress}% - {message}")
                            last_progress = progress
                
                if status.get('status') == 'completed':
                    print("Job completed!")
                    break
                elif status.get('status') == 'failed':
                    print(f"Job failed: {status.get('error', 'Unknown error')}")
                    break
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(1)
        
        # Get final result
        if status.get('status') == 'completed':
            print("\n=== FINAL RESULTS ===")
            print(f"Status: {status.get('status')}")
            
            if 'result' in status:
                result = status['result']
                citations = result.get('citations', [])
                clusters = result.get('clusters', [])
                
                print(f"Total citations extracted: {len(citations)}")
                print(f"Total clusters created: {len(clusters)}")
                
                # Count verified citations
                verified_count = sum(1 for c in citations if c.get('verified'))
                print(f"Citations verified: {verified_count}/{len(citations)}")
                
                # Show first few citations
                print("\nFirst 5 citations:")
                for i, cit in enumerate(citations[:5]):
                    print(f"  {i+1}. {cit.get('citation', 'N/A')} - Verified: {cit.get('verified', False)}")
                    if cit.get('canonical_name'):
                        print(f"     Canonical: {cit.get('canonical_name')} ({cit.get('canonical_date', 'N/A')})")
                
                # Show cluster summary
                if clusters:
                    print("\nCluster summary:")
                    for i, cluster in enumerate(clusters[:3]):
                        cluster_size = len(cluster.get('citations', []))
                        verified = cluster.get('verification_status') == 'verified'
                        print(f"  Cluster {i+1}: {cluster_size} citations, Verified: {verified}")
        
        # Summary
        print("\nProgress Update Summary:")
        print(f"Total progress updates: {len(progress_updates)}")
        for progress, message in progress_updates:
            print(f"  {progress}% - {message}")
            
        if len(progress_updates) <= 3:
            print("\n⚠️  WARNING: Progress bar appears stuck (only 3 or fewer updates)")
        else:
            print("\n✅ Progress updates working correctly!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close file
        if 'files' in locals():
            files['file'].close()

if __name__ == "__main__":
    test_pdf_processing()
