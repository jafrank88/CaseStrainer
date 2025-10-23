#!/usr/bin/env python3
"""
Test Sync vs Async Pathway Consistency

This script tests both processing pathways to ensure they produce identical output.
"""
import requests
import json
import time
from typing import Dict, Any

# Disable SSL warnings for localhost testing
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost/casestrainer/api"

def test_sync_pathway(text: str) -> Dict[str, Any]:
    """Test the sync (immediate) pathway with short text."""
    print("\n" + "="*60)
    print("TESTING SYNC PATHWAY (Short Text)")
    print("="*60)
    
    url = f"{BASE_URL}/analyze"
    data = {
        "type": "text",
        "text": text
    }
    
    print(f"📤 Sending: {text}")
    start = time.time()
    
    try:
        response = requests.post(url, json=data, verify=False, timeout=30)
        elapsed = time.time() - start
        
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


def test_async_pathway(text: str) -> Dict[str, Any]:
    """Test the async (queued) pathway by forcing it with a large input."""
    print("\n" + "="*60)
    print("TESTING ASYNC PATHWAY (Force with padding)")
    print("="*60)
    
    # Pad the text to force async processing (>5000 chars)
    padding = "\n\n" + ("Lorem ipsum dolor sit amet. " * 200)  # ~5600 chars
    padded_text = text + padding
    
    url = f"{BASE_URL}/analyze"
    data = {
        "type": "text",
        "text": padded_text
    }
    
    print(f"📤 Sending: {text[:50]}... (padded to {len(padded_text)} chars)")
    start = time.time()
    
    try:
        response = requests.post(url, json=data, verify=False, timeout=60)
        elapsed = time.time() - start
        
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            # If queued, wait for completion
            if result.get('status') == 'queued':
                task_id = result.get('task_id')
                print(f"⏳ Queued as task: {task_id}")
                print("⏳ Waiting for completion...")
                
                # Poll for results
                max_wait = 60
                for i in range(max_wait):
                    time.sleep(1)
                    status_url = f"{BASE_URL}/task_status/{task_id}"
                    status_resp = requests.get(status_url, verify=False)
                    
                    if status_resp.status_code == 200:
                        status_data = status_resp.json()
                        if status_data.get('status') == 'completed':
                            print(f"✅ Completed after {i+1}s")
                            return status_data.get('result', {})
                        elif status_data.get('status') == 'failed':
                            print(f"❌ Task failed: {status_data.get('error')}")
                            return None
                    
                    if i % 5 == 0:
                        print(f"⏳ Still waiting... ({i}s)")
                
                print("⏱️ Timeout waiting for async task")
                return None
            else:
                return result
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


def compare_results(sync_result: Dict, async_result: Dict, test_name: str):
    """Compare outputs from sync and async pathways."""
    print("\n" + "="*60)
    print(f"COMPARISON: {test_name}")
    print("="*60)
    
    if not sync_result or not async_result:
        print("❌ Cannot compare - one or both results missing")
        return False
    
    # Extract key data
    sync_citations = sync_result.get('result', {}).get('citations', [])
    async_citations = async_result.get('result', {}).get('citations', [])
    
    sync_clusters = sync_result.get('result', {}).get('clusters', [])
    async_clusters = async_result.get('result', {}).get('clusters', [])
    
    print(f"\n📊 CITATIONS COUNT:")
    print(f"  Sync:  {len(sync_citations)}")
    print(f"  Async: {len(async_citations)}")
    
    print(f"\n📊 CLUSTERS COUNT:")
    print(f"  Sync:  {len(sync_clusters)}")
    print(f"  Async: {len(async_clusters)}")
    
    # Check citation structure
    if sync_citations and async_citations:
        sync_cit = sync_citations[0]
        async_cit = async_citations[0]
        
        print(f"\n🔍 FIRST CITATION COMPARISON:")
        print(f"  Citation Text:")
        print(f"    Sync:  {sync_cit.get('citation', 'N/A')}")
        print(f"    Async: {async_cit.get('citation', 'N/A')}")
        
        print(f"\n  Extracted Case Name:")
        sync_extracted = sync_cit.get('extracted_case_name', 'N/A')
        async_extracted = async_cit.get('extracted_case_name', 'N/A')
        print(f"    Sync:  {sync_extracted}")
        print(f"    Async: {async_extracted}")
        
        if sync_extracted == async_extracted:
            print(f"    ✅ MATCH!")
        else:
            print(f"    ❌ MISMATCH!")
        
        print(f"\n  Extracted Date:")
        sync_date = sync_cit.get('extracted_date', 'N/A')
        async_date = async_cit.get('extracted_date', 'N/A')
        print(f"    Sync:  {sync_date}")
        print(f"    Async: {async_date}")
        
        if sync_date == async_date:
            print(f"    ✅ MATCH!")
        else:
            print(f"    ❌ MISMATCH!")
    
    # Check cluster structure
    if sync_clusters and async_clusters:
        sync_cluster = sync_clusters[0]
        async_cluster = async_clusters[0]
        
        print(f"\n🔍 FIRST CLUSTER COMPARISON:")
        
        print(f"\n  Extracted Case Name:")
        sync_cluster_extracted = sync_cluster.get('extracted_case_name', 'N/A')
        async_cluster_extracted = async_cluster.get('extracted_case_name', 'N/A')
        print(f"    Sync:  {sync_cluster_extracted}")
        print(f"    Async: {async_cluster_extracted}")
        
        if sync_cluster_extracted == async_cluster_extracted:
            print(f"    ✅ MATCH!")
        else:
            print(f"    ❌ MISMATCH!")
        
        print(f"\n  Extracted Date:")
        sync_cluster_date = sync_cluster.get('extracted_date', 'N/A')
        async_cluster_date = async_cluster.get('extracted_date', 'N/A')
        print(f"    Sync:  {sync_cluster_date}")
        print(f"    Async: {async_cluster_date}")
        
        if sync_cluster_date == async_cluster_date:
            print(f"    ✅ MATCH!")
        else:
            print(f"    ❌ MISMATCH!")
        
        # CRITICAL: Check if cluster.citations array contains extracted_case_name
        print(f"\n  Cluster Citations Array:")
        sync_cluster_cits = sync_cluster.get('citations', [])
        async_cluster_cits = async_cluster.get('citations', [])
        
        print(f"    Sync citations count:  {len(sync_cluster_cits)}")
        print(f"    Async citations count: {len(async_cluster_cits)}")
        
        if sync_cluster_cits:
            sync_first_cit = sync_cluster_cits[0]
            print(f"\n    Sync cluster.citations[0]:")
            print(f"      Type: {type(sync_first_cit)}")
            if isinstance(sync_first_cit, dict):
                print(f"      ✅ Is dict (Vue.js can read it)")
                print(f"      extracted_case_name: {sync_first_cit.get('extracted_case_name', 'MISSING')}")
            else:
                print(f"      ❌ Is {type(sync_first_cit).__name__} (Vue.js CANNOT read it!)")
        
        if async_cluster_cits:
            async_first_cit = async_cluster_cits[0]
            print(f"\n    Async cluster.citations[0]:")
            print(f"      Type: {type(async_first_cit)}")
            if isinstance(async_first_cit, dict):
                print(f"      ✅ Is dict (Vue.js can read it)")
                print(f"      extracted_case_name: {async_first_cit.get('extracted_case_name', 'MISSING')}")
            else:
                print(f"      ❌ Is {type(async_first_cit).__name__} (Vue.js CANNOT read it!)")
    
    # Overall verdict
    print(f"\n" + "="*60)
    print("VERDICT:")
    print("="*60)
    
    issues = []
    if len(sync_citations) != len(async_citations):
        issues.append("Citation count mismatch")
    if len(sync_clusters) != len(async_clusters):
        issues.append("Cluster count mismatch")
    if sync_citations and async_citations:
        if sync_citations[0].get('extracted_case_name') != async_citations[0].get('extracted_case_name'):
            issues.append("Citation extracted_case_name mismatch")
    if sync_clusters and async_clusters:
        if sync_clusters[0].get('extracted_case_name') != async_clusters[0].get('extracted_case_name'):
            issues.append("Cluster extracted_case_name mismatch")
    
    if not issues:
        print("✅ PATHWAYS ARE CONSISTENT!")
        return True
    else:
        print("❌ PATHWAYS HAVE DIFFERENCES:")
        for issue in issues:
            print(f"  - {issue}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("SYNC vs ASYNC PATHWAY CONSISTENCY TEST")
    print("="*60)
    print("\nThis test will submit the same text through both pathways")
    print("and verify they produce identical output.\n")
    
    # Test case
    test_text = "Carman v. Adventure Bound, 198 Cal.App.3d 449 (1986)"
    
    # Run tests
    sync_result = test_sync_pathway(test_text)
    async_result = test_async_pathway(test_text)
    
    # Compare
    success = compare_results(sync_result, async_result, "Carman v. Adventure Bound")
    
    # Save detailed output
    print("\n" + "="*60)
    print("SAVING DETAILED OUTPUT")
    print("="*60)
    
    output = {
        'test_text': test_text,
        'sync_result': sync_result,
        'async_result': async_result,
        'consistent': success
    }
    
    with open('pathway_test_results.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)
    
    print("✅ Saved to: pathway_test_results.json")
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    if success:
        print("✅ SUCCESS: Both pathways are consistent!")
        print("   The sync/async unification is working correctly.")
    else:
        print("❌ FAILURE: Pathways produce different output!")
        print("   Review pathway_test_results.json for details.")
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
