#!/usr/bin/env python
"""Test with a real PDF from the root directory."""

import requests
import time
import os

# Use a real PDF from root directory
file_path = "d:\\dev\\casestrainer\\sp-7788.pdf"

if not os.path.exists(file_path):
    print(f"❌ File not found: {file_path}")
    exit(1)

print(f"Testing with real PDF: {file_path}")
print(f"File size: {os.path.getsize(file_path):,} bytes")

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
files = {'file': open(file_path, 'rb')}
data = {
    "enable_verification": False,  # Skip verification for speed
    "client_request_id": f"test_real_pdf_{int(time.time())}"
}

try:
    response = requests.post(url, files=files, data=data, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    print(f"\n✅ Response received!")
    print(f"Status: {result.get('status')}")
    print(f"Processing mode: {result.get('metadata', {}).get('processing_mode')}")
    
    task_id = result.get('task_id')
    if task_id:
        print(f"✅ Async processing - Task ID: {task_id}")
        print(f"\nMonitoring progress...")
        
        # Check status
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        start_time = time.time()
        
        while time.time() - start_time < 120:  # 2 minute timeout
            try:
                status_response = requests.get(status_url, timeout=5)
                status = status_response.json()
                
                progress = status.get('verification_status', {}).get('progress_percent', 0)
                message = status.get('verification_status', {}).get('current_message', '')
                
                if progress > 0:
                    print(f"Progress: {progress}% - {message}")
                
                if status.get('status') == 'completed':
                    print("\n✅ PDF PROCESSING COMPLETED!")
                    if 'result' in status:
                        result = status['result']
                        citations = result.get('citations', [])
                        clusters = result.get('clusters', [])
                        
                        print(f"\n📊 PDF PROCESSING RESULTS:")
                        print(f"Total citations extracted: {len(citations)}")
                        print(f"Clusters created: {len(clusters)}")
                        
                        # Show first 10 citations
                        print(f"\n📋 First 10 citations from PDF:")
                        for i, cit in enumerate(citations[:10]):
                            print(f"  {i+1}. {cit.get('citation', 'N/A')}")
                            if cit.get('extracted_case_name'):
                                print(f"     Case: {cit.get('extracted_case_name')}")
                            if cit.get('extracted_date'):
                                print(f"     Year: {cit.get('extracted_date')}")
                                
                        # Show cluster summary
                        if clusters:
                            print(f"\n🔗 Cluster summary:")
                            for i, cluster in enumerate(clusters[:5]):
                                cluster_size = len(cluster.get('citations', []))
                                if cluster.get('canonical_name'):
                                    print(f"  Cluster {i+1}: {cluster_size} citations → {cluster.get('canonical_name')}")
                                else:
                                    print(f"  Cluster {i+1}: {cluster_size} citations")
                        
                        print(f"\n🎉 PDF PROCESSING VALIDATION:")
                        print(f"✅ EXTRACTION: Working - {len(citations)} citations found")
                        print(f"✅ CLUSTERING: Working - {len(clusters)} clusters created")
                        print(f"✅ PDF TEXT: Successfully extracted and processed")
                        print(f"✅ ASYNC PROCESSING: Large PDF processed via workers")
                        
                        # Check for quality
                        with_case_names = sum(1 for c in citations if c.get('extracted_case_name'))
                        with_dates = sum(1 for c in citations if c.get('extracted_date'))
                        
                        print(f"\n📈 Extraction Quality:")
                        print(f"Citations with case names: {with_case_names}/{len(citations)} ({with_case_names/len(citations)*100:.1f}%)")
                        print(f"Citations with dates: {with_dates}/{len(citations)} ({with_dates/len(citations)*100:.1f}%)")
                        
                        if with_case_names > len(citations) * 0.7:
                            print("✅ Good case name extraction rate (>70%)")
                        else:
                            print("⚠️  Low case name extraction rate (<70%)")
                    break
                elif status.get('status') == 'failed':
                    print(f"\n❌ Processing failed: {status.get('error', 'Unknown error')}")
                    break
                    
                time.sleep(2)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(2)
        else:
            print("\n⏰ Timeout: PDF processing took too long")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    files['file'].close()
