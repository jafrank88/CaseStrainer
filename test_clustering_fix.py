#!/usr/bin/env python3
"""
Comprehensive test to verify clustering fix works for both sync and async modes.
"""

import requests
import json
import time

def test_clustering_fix():
    """Test citation clustering fix with detailed analysis."""
    test_text = '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)'''

    payload = {
        "type": "text",
        "text": test_text
    }

    headers = {
        "Content-Type": "application/json"
    }

    print("🚀 Testing Citation Clustering Fix")
    print("="*60)
    
    # Test different backend URLs
    urls = [
        "http://localhost:5001/casestrainer/api/analyze",
        "http://localhost:80/casestrainer/api/analyze", 
        "http://localhost/casestrainer/api/analyze",
        "https://localhost/casestrainer/api/analyze"
    ]

    for url in urls:
        print(f"\n🧪 Testing: {url}")
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success!")
                
                # Analyze the response
                success = analyze_clustering_response(data, url)
                if success:
                    return True
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    print("\n❌ No working endpoints found!")
    return False

def analyze_clustering_response(data, url):
    """Analyze clustering response in detail."""
    print(f"\n📊 DETAILED ANALYSIS")
    print("="*50)
    
    citations = data.get('citations', [])
    clusters = data.get('clusters', [])
    
    print(f"Total citations: {len(citations)}")
    print(f"Total clusters: {len(clusters)}")
    
    # Check metadata in citations
    citations_with_metadata = 0
    citations_in_clusters = 0
    
    print(f"\n📋 Citation Analysis:")
    for i, citation in enumerate(citations):
        citation_text = citation.get('citation', 'N/A')
        metadata = citation.get('metadata', {})
        
        if metadata:
            citations_with_metadata += 1
            if metadata.get('is_in_cluster'):
                citations_in_clusters += 1
                cluster_id = metadata.get('cluster_id', 'unknown')
                cluster_size = metadata.get('cluster_size', 0)
                print(f"  {i+1:2d}. ✅ IN CLUSTER {cluster_id} (size: {cluster_size}) - {citation_text}")
            else:
                print(f"  {i+1:2d}. ❌ NO CLUSTER - {citation_text}")
        else:
            print(f"  {i+1:2d}. ❌ NO METADATA - {citation_text}")
    
    print(f"\n📈 Summary:")
    print(f"  Citations with metadata: {citations_with_metadata}/{len(citations)}")
    print(f"  Citations in clusters: {citations_in_clusters}/{len(citations)}")
    
    # Analyze clusters
    if clusters:
        print(f"\n🔗 Cluster Details:")
        for i, cluster in enumerate(clusters):
            cluster_id = cluster.get('cluster_id', f'cluster_{i}')
            cluster_size = len(cluster.get('citations', []))
            canonical_name = cluster.get('canonical_name', 'N/A')
            extracted_date = cluster.get('extracted_date', 'N/A')
            
            print(f"  Cluster {i+1} ({cluster_id}): {cluster_size} citations")
            print(f"    Case: {canonical_name}")
            print(f"    Date: {extracted_date}")
            
            # Show cluster members
            for citation in cluster.get('citations', []):
                citation_text = citation.get('citation', 'N/A')
                print(f"      - {citation_text}")
            print()
    else:
        print(f"\n❌ No clusters found!")
    
    # Check for success criteria
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
        print(f"\n🎉 PERFECT! Clustering is working correctly!")
        print(f"  ✅ 3 clusters found")
        print(f"  ✅ {citations_in_clusters} citations have cluster metadata")
        print(f"  ✅ All clusters have 2+ citations")
        print(f"  ✅ Frontend should display clusters correctly")
        return True

def test_async_mode():
    """Test async processing mode specifically."""
    print("\n🔄 Testing Async Mode")
    print("="*40)
    
    test_text = '''A federal court may ask this court to answer a question of Washington law when a resolution of that question is necessary to resolve a case before the federal court. RCW 2.60.020; Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions are questions of law we review de novo. Carlson v. Glob. Client Sols., LLC, 171 Wn.2d 486, 493, 256 P.3d 321 (2011). We also review the meaning of a statute de novo. Dep't of Ecology v. Campbell & Gwinn, LLC, 146 Wn.2d 1, 9, 43 P.3d 4 (2003)'''

    payload = {
        "type": "text",
        "text": test_text
    }

    headers = {
        "Content-Type": "application/json"
    }

    url = "http://localhost:5001/casestrainer/api/analyze"
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if it's async
            if data.get('status') == 'processing' and data.get('task_id'):
                task_id = data['task_id']
                print(f"✅ Async task submitted: {task_id}")
                
                # Poll for results
                return poll_async_results(url, task_id)
            else:
                print(f"✅ Immediate response (sync mode)")
                return analyze_clustering_response(data, url)
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def poll_async_results(base_url, task_id):
    """Poll for async task results."""
    print(f"⏳ Polling for results...")
    
    for attempt in range(30):  # Poll for up to 30 seconds
        try:
            status_url = f"{base_url}/casestrainer/api/task_status/{task_id}"
            response = requests.get(status_url, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get('status')
                
                if status == 'completed':
                    print(f"✅ Task completed!")
                    return analyze_clustering_response(status_data, base_url)
                elif status == 'failed':
                    print(f"❌ Task failed: {status_data.get('error', 'Unknown error')}")
                    return False
                else:
                    print(f"⏳ Status: {status}")
            
            time.sleep(1)
        except Exception as e:
            print(f"⚠️  Poll error: {e}")
            time.sleep(1)
    
    print(f"❌ Polling timed out")
    return False

def main():
    """Main test function."""
    print("🚀 Testing Citation Clustering Fix - Sync and Async")
    print("="*70)
    
    # Test sync mode
    sync_success = test_clustering_fix()
    
    if sync_success:
        print("\n" + "="*70)
        # Test async mode
        async_success = test_async_mode()
        
        print("\n" + "="*70)
        print("FINAL RESULTS")
        print("="*70)
        print(f"Sync mode: {'✅ PASS' if sync_success else '❌ FAIL'}")
        print(f"Async mode: {'✅ PASS' if async_success else '❌ FAIL'}")
        
        if sync_success and async_success:
            print("\n🎉 Both modes working correctly!")
            print("✅ Frontend should now display clusters properly")
            return True
        else:
            print("\n⚠️  Some issues found")
            return False
    else:
        print("\n❌ Sync mode failed - need to fix clustering")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 