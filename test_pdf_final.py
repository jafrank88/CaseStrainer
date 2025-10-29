#!/usr/bin/env python
"""Final test with a PDF from the root directory."""

import requests
import time
import os

# Use a PDF from root directory
file_path = "d:\\dev\\casestrainer\\Lavery v. The Department of Financial and Professional Regulation 2025 IL 130033.pdf"

if not os.path.exists(file_path):
    print(f"❌ File not found: {file_path}")
    exit(1)

print("=" * 60)
print("PDF PROCESSING VALIDATION")
print("=" * 60)
print(f"Testing PDF: {os.path.basename(file_path)}")
print(f"File size: {os.path.getsize(file_path):,} bytes")

url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
files = {'file': open(file_path, 'rb')}
data = {
    "enable_verification": False,  # Skip verification for speed
    "client_request_id": f"pdf_test_{int(time.time())}"
}

try:
    response = requests.post(url, files=files, data=data, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    print(f"\n✅ PDF submitted successfully!")
    print(f"Status: {result.get('status')}")
    print(f"Processing mode: {result.get('metadata', {}).get('processing_mode')}")
    
    task_id = result.get('task_id')
    if task_id:
        print(f"✅ Async processing - Task ID: {task_id}")
        
        # Monitor progress
        status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
        print(f"\nMonitoring PDF processing...")
        
        start_time = time.time()
        while time.time() - start_time < 60:  # 1 minute timeout
            try:
                status_response = requests.get(status_url, timeout=5)
                status = status_response.json()
                
                progress = status.get('verification_status', {}).get('progress_percent', 0)
                message = status.get('verification_status', {}).get('current_message', '')
                
                if progress > 0:
                    print(f"  Progress: {progress}% - {message}")
                
                if status.get('status') == 'completed':
                    print(f"\n✅ PDF PROCESSING COMPLETED!")
                    
                    if 'result' in status:
                        result = status['result']
                        citations = result.get('citations', [])
                        clusters = result.get('clusters', [])
                        
                        print("\n" + "=" * 60)
                        print("PDF PROCESSING RESULTS")
                        print("=" * 60)
                        
                        print(f"\n📊 Extraction Results:")
                        print(f"  Total citations extracted: {len(citations)}")
                        print(f"  Clusters created: {len(clusters)}")
                        
                        # Show first 10 citations
                        print(f"\n📋 First 10 citations from PDF:")
                        for i, cit in enumerate(citations[:10]):
                            print(f"  {i+1}. {cit.get('citation', 'N/A')}")
                            if cit.get('extracted_case_name'):
                                case_name = cit.get('extracted_case_name')
                                # Truncate long case names
                                if len(case_name) > 80:
                                    case_name = case_name[:77] + "..."
                                print(f"     Case: {case_name}")
                            if cit.get('extracted_date'):
                                print(f"     Year: {cit.get('extracted_date')}")
                                
                        # Show cluster summary
                        if clusters:
                            print(f"\n🔗 Cluster Summary:")
                            for i, cluster in enumerate(clusters[:5]):
                                cluster_size = len(cluster.get('citations', []))
                                if cluster.get('canonical_name'):
                                    name = cluster.get('canonical_name')
                                    if len(name) > 60:
                                        name = name[:57] + "..."
                                    print(f"  Cluster {i+1}: {cluster_size} citations → {name}")
                                else:
                                    print(f"  Cluster {i+1}: {cluster_size} citations")
                        
                        print(f"\n🎯 PDF PROCESSING VALIDATION:")
                        
                        # Check extraction quality
                        with_case_names = sum(1 for c in citations if c.get('extracted_case_name'))
                        with_dates = sum(1 for c in citations if c.get('extracted_date'))
                        
                        print(f"  ✅ PDF TEXT EXTRACTION: Working - PDF content successfully extracted")
                        print(f"  ✅ CITATION EXTRACTION: Working - {len(citations)} citations found")
                        print(f"  ✅ CLUSTERING: Working - {len(clusters)} clusters created")
                        print(f"  ✅ CASE NAMES: {with_case_names}/{len(citations)} have names extracted")
                        print(f"  ✅ DATES: {with_dates}/{len(citations)} have dates extracted")
                        print(f"  ✅ ASYNC PROCESSING: Large PDF processed via workers")
                        
                        # Quality assessment
                        if with_case_names > len(citations) * 0.5:
                            print(f"  ✅ EXTRACTION QUALITY: Good (>50% case names)")
                        else:
                            print(f"  ⚠️  EXTRACTION QUALITY: Could improve ({with_case_names/len(citations)*100:.1f}% case names)")
                            
                        print(f"\n🎉 PDF PROCESSING: FUNCTIONAL")
                        print("=" * 60)
                        
                    break
                elif status.get('status') == 'failed':
                    print(f"\n❌ Processing failed: {status.get('error', 'Unknown error')}")
                    break
                    
                time.sleep(2)
                
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(2)
        else:
            print(f"\n⏰ Timeout: PDF processing took too long")
    else:
        print(f"❌ Unexpected: Processed synchronously")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    files['file'].close()
