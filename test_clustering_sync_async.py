#!/usr/bin/env python3
"""
Test script to verify citation clustering works in both synchronous and asynchronous modes.
"""

import requests
import json
import time

def test_sync_mode():
    """Test synchronous citation processing."""
    print("🧪 Testing SYNCHRONOUS mode...")
    
    test_text = '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)'''

    payload = {
        "type": "text",
        "text": test_text
    }

    headers = {
        "Content-Type": "application/json"
    }

    # Test different backend URLs
    urls = [
        "http://localhost:5001/casestrainer/api/analyze",
        "http://localhost:80/casestrainer/api/analyze", 
        "http://localhost/casestrainer/api/analyze",
        "https://localhost/casestrainer/api/analyze"
    ]

    for url in urls:
        print(f"  Testing: {url}")
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Success!")
                return analyze_response(data, "SYNC")
            else:
                print(f"  ❌ Error: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Connection error: {e}")
    
    return None

def test_async_mode():
    """Test asynchronous citation processing."""
    print("🧪 Testing ASYNCHRONOUS mode...")
    
    test_text = '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)'''

    payload = {
        "type": "text",
        "text": test_text
    }

    headers = {
        "Content-Type": "application/json"
    }

    # Test different backend URLs
    urls = [
        "http://localhost:5001/casestrainer/api/analyze",
        "http://localhost:80/casestrainer/api/analyze", 
        "http://localhost/casestrainer/api/analyze",
        "https://localhost/casestrainer/api/analyze"
    ]

    for url in urls:
        print(f"  Testing: {url}")
        try:
            # First, submit the task
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                # Check if it's async (has task_id and status 'processing')
                if data.get('status') == 'processing' and data.get('task_id'):
                    task_id = data['task_id']
                    print(f"  ✅ Async task submitted: {task_id}")
                    
                    # Poll for results
                    return poll_async_results(url, task_id, "ASYNC")
                else:
                    print(f"  ✅ Immediate response (sync mode)")
                    return analyze_response(data, "ASYNC")
            else:
                print(f"  ❌ Error: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Connection error: {e}")
    
    return None

def poll_async_results(base_url, task_id, mode):
    """Poll for async task results."""
    print(f"  ⏳ Polling for results...")
    
    for attempt in range(30):  # Poll for up to 30 seconds
        try:
            # Check task status
            status_url = f"{base_url}/casestrainer/api/task_status/{task_id}"
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                
                if status == 'completed':
                    print(f"  ✅ Task completed!")
                    return analyze_response(status_data, mode)
                elif status == 'failed':
                    print(f"  ❌ Task failed: {status_data.get('error', 'Unknown error')}")
                    return None
                else:
                    print(f"  ⏳ Status: {status}")
            
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️  Poll error: {e}")
            time.sleep(1)
    
    print(f"  ❌ Polling timed out")
    return None

def analyze_response(data, mode):
    """Analyze the response for clustering issues."""
    print(f"\n📊 ANALYSIS ({mode} MODE)")
    print("="*50)
    
    citations = data.get('citations', [])
    clusters = data.get('clusters', [])
    
    print(f"Total citations: {len(citations)}")
    print(f"Total clusters: {len(clusters)}")
    
    # Check metadata in citations
    citations_with_metadata = 0
    citations_in_clusters = 0
    
    for i, citation in enumerate(citations):
        metadata = citation.get('metadata', {})
        if metadata:
            citations_with_metadata += 1
            if metadata.get('is_in_cluster'):
                citations_in_clusters += 1
                print(f"  Citation {i+1}: IN CLUSTER {metadata.get('cluster_id')}")
            else:
                print(f"  Citation {i+1}: NO CLUSTER")
        else:
            print(f"  Citation {i+1}: NO METADATA")
    
    print(f"\nCitations with metadata: {citations_with_metadata}/{len(citations)}")
    print(f"Citations in clusters: {citations_in_clusters}/{len(citations)}")
    
    # Analyze clusters
    if clusters:
        print(f"\nCluster details:")
        for i, cluster in enumerate(clusters):
            cluster_size = len(cluster.get('citations', []))
            cluster_id = cluster.get('cluster_id', f'cluster_{i}')
            print(f"  Cluster {i+1} ({cluster_id}): {cluster_size} citations")
            
            # Show cluster members
            for citation in cluster.get('citations', []):
                print(f"    - {citation.get('citation', 'N/A')}")
    else:
        print(f"\n❌ No clusters found!")
    
    # Check for issues
    issues = []
    if len(clusters) != 3:
        issues.append(f"Expected 3 clusters, got {len(clusters)}")
    
    if citations_in_clusters == 0:
        issues.append("No citations have cluster metadata")
    
    cluster_sizes = [len(cluster.get('citations', [])) for cluster in clusters]
    if not all(size >= 2 for size in cluster_sizes):
        issues.append(f"Clusters too small: {cluster_sizes}")
    
    if issues:
        print(f"\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"\n✅ PERFECT! 3 clusters with 2+ cases each")
        return True

def main():
    """Main test function."""
    print("🚀 Testing Citation Clustering - Sync vs Async")
    print("="*60)
    
    # Test sync mode
    sync_success = test_sync_mode()
    
    print("\n" + "="*60)
    
    # Test async mode  
    async_success = test_async_mode()
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    print(f"Sync mode: {'✅ PASS' if sync_success else '❌ FAIL'}")
    print(f"Async mode: {'✅ PASS' if async_success else '❌ FAIL'}")
    
    if sync_success and async_success:
        print("\n🎉 Both modes working correctly!")
        return True
    else:
        print("\n⚠️  Issues found - need to fix clustering logic")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 