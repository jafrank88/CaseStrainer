"""Test with the user's actual document: 24-2626.pdf"""
import requests
import json

pdf_path = "D:/dev/casestrainer/24-2626.pdf"
url = "http://localhost:5000/casestrainer/api/analyze"

print("=" * 80)
print("TESTING USER'S DOCUMENT: 24-2626.pdf")
print("=" * 80)
print()

# Upload the PDF with sync processing forced
with open(pdf_path, 'rb') as f:
    files = {'file': ('24-2626.pdf', f, 'application/pdf')}
    data = {
        'force_sync': 'true',
        'process_immediately': 'true'  # Force sync processing
    }
    
    print("[UPLOAD] Uploading 24-2626.pdf (forcing sync processing)...")
    response = requests.post(url, files=files, data=data, timeout=300)

print(f"[STATUS] Response: {response.status_code}")
print()

if response.status_code == 200:
    result = response.json()
    
    # Check if it was queued for async processing
    processing_mode = result.get('metadata', {}).get('processing_mode', 'immediate')
    task_id = result.get('request_id') or result.get('metadata', {}).get('job_id')
    
    if processing_mode == 'queued' and task_id:
        print(f"[ASYNC] Task queued: {task_id}")
        print("[WAITING] Polling for results...")
        
        import time
        poll_url = f"http://localhost:5000/casestrainer/api/task/{task_id}"
        max_attempts = 60
        
        for i in range(max_attempts):
            time.sleep(2)
            poll_response = requests.get(poll_url)
            if poll_response.status_code == 200:
                poll_result = poll_response.json()
                status = poll_result.get('status', 'unknown')
                progress = poll_result.get('progress_data', {}).get('overall_progress', 0)
                print(f"  [{i+1}] Status: {status}, Progress: {progress}%")
                
                if status == 'completed':
                    result = poll_result.get('result', {})
                    print("[ASYNC] Processing completed!")
                    break
                elif status in ('failed', 'error'):
                    print(f"[ERROR] Task failed: {poll_result.get('error')}")
                    exit(1)
        else:
            print("[TIMEOUT] Task did not complete in time")
            exit(1)
    
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"[RESULTS]")
    print(f"  Total Citations: {len(citations)}")
    print(f"  Total Clusters: {len(clusters)}")
    print()
    
    # Check for the specific issues user reported
    print("[CHECKING REPORTED ISSUES]")
    print("-" * 80)
    
    # Issue 1: False clustering of F.3d citations
    print("\n1. False Clustering Check (783 F.3d, 936 F.3d, 910 F.3d):")
    f3d_citations = [c for c in citations if 'F.3d' in c.get('citation', '')]
    f3d_problematic = [c for c in f3d_citations if any(vol in c.get('citation', '') for vol in ['783', '936', '910'])]
    
    if f3d_problematic:
        print(f"  Found {len(f3d_problematic)} potentially problematic F.3d citations:")
        for cite in f3d_problematic:
            citation_text = cite.get('citation', '')
            case_name = cite.get('extracted_case_name', 'N/A')
            cluster_id = cite.get('cluster_id', 'none')
            print(f"    • {citation_text}: {case_name} (cluster: {cluster_id})")
        
        # Check if they're in the same cluster
        cluster_ids = [c.get('cluster_id') for c in f3d_problematic if c.get('cluster_id')]
        if len(set(cluster_ids)) == 1 and len(cluster_ids) > 1:
            print(f"  ❌ STILL CLUSTERED TOGETHER (cluster {cluster_ids[0]})")
        else:
            print(f"  ✅ CORRECTLY SEPARATED into different clusters")
    else:
        print("  No F.3d citations found matching 783/936/910")
    
    # Issue 2: N/A extractions
    print("\n2. N/A Extraction Check:")
    na_citations = [c for c in citations if c.get('extracted_case_name') == 'N/A']
    if na_citations:
        print(f"  Found {len(na_citations)} citations with N/A:")
        for cite in na_citations[:5]:  # Show first 5
            citation_text = cite.get('citation', '')
            print(f"    • {citation_text}: N/A")
        if len(na_citations) > 5:
            print(f"    ... and {len(na_citations) - 5} more")
    else:
        print("  ✅ NO N/A EXTRACTIONS FOUND")
    
    # Issue 3: Check for 897 F.3d 1224 specifically
    print("\n3. Specific Citation Check (897 F.3d 1224):")
    cite_897 = next((c for c in citations if '897 F.3d 1224' in c.get('citation', '')), None)
    if cite_897:
        case_name = cite_897.get('extracted_case_name', 'N/A')
        verified = cite_897.get('verified', False)
        print(f"  Citation: 897 F.3d 1224")
        print(f"  Extracted: {case_name}")
        print(f"  Verified: {'✅' if verified else '❌'}")
        print(f"  Status: {'GOOD' if case_name != 'N/A' else 'N/A ISSUE'}")
    else:
        print("  Citation 897 F.3d 1224 not found in document")
    
    # Show sample of clusters
    print("\n4. Sample Clusters:")
    print("-" * 80)
    for i, cluster in enumerate(clusters[:10], 1):
        case_name = cluster.get('case_name', 'N/A')
        citations_in_cluster = cluster.get('citations', [])
        citation_texts = [c.get('text', '') for c in citations_in_cluster]
        print(f"  Cluster {i}: {case_name}")
        print(f"    Citations: {', '.join(citation_texts)}")
    
    if len(clusters) > 10:
        print(f"  ... and {len(clusters) - 10} more clusters")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    na_count = len(na_citations)
    na_percent = (na_count / len(citations) * 100) if citations else 0
    print(f"  Total Citations: {len(citations)}")
    print(f"  N/A Extractions: {na_count} ({na_percent:.1f}%)")
    print(f"  Total Clusters: {len(clusters)}")
    print()
    
    if na_count == 0:
        print("  ✅ No N/A extractions - truncation fix working!")
    elif na_count < 5:
        print("  ⚠️  Few N/A extractions - mostly working")
    else:
        print("  ❌ Multiple N/A extractions - may need investigation")

else:
    print(f"[ERROR] Upload failed: {response.status_code}")
    print(response.text)
