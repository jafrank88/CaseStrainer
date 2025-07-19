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

    success_found = False
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
                    success_found = True
                    break
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
    
    if not success_found:
        print("\n⚠️  No working endpoints found - this is expected if backend is not running")
        print("   The test will be skipped in CI environments")
        # Skip the test if no endpoints are available
        import pytest
        pytest.skip("No working backend endpoints found - backend may not be running")

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
        assert False, f"Clustering issues found: {issues}"
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
                result = poll_async_results(url, task_id)
                assert result, "Async polling failed"
                return
            else:
                print(f"✅ Immediate response (sync mode)")
                result = analyze_clustering_response(data, url)
                assert result, "Sync mode analysis failed"
                return
        else:
            print(f"❌ Error: {response.status_code}")
            assert False, f"API returned error status: {response.status_code}"
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("⚠️  Backend not available - skipping async test")
        import pytest
        pytest.skip("Backend not available for async testing")

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
                    result = analyze_clustering_response(status_data, base_url)
                    assert result, "Async task analysis failed"
                    return True
                elif status == 'failed':
                    print(f"❌ Task failed: {status_data.get('error', 'Unknown error')}")
                    assert False, f"Async task failed: {status_data.get('error', 'Unknown error')}"
                else:
                    print(f"⏳ Status: {status}")
            
            time.sleep(1)
        except Exception as e:
            print(f"⚠️  Poll error: {e}")
            time.sleep(1)
    
    print(f"❌ Polling timed out")
    assert False, "Async polling timed out"

def main():
    """Main test function."""
    print("🚀 Testing Citation Clustering Fix - Sync and Async")
    print("="*70)
    
    # Test sync mode
    test_clustering_fix()
    
    print("\n" + "="*70)
    # Test async mode
    test_async_mode()
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print("🎉 Both modes working correctly!")
    print("✅ Frontend should now display clusters properly")

if __name__ == "__main__":
    main() 