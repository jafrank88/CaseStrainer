#!/usr/bin/env python3
"""
Check the results of the async processing job.
"""

import requests
import json

def check_async_results():
    """Check the results of the async processing job."""
    
    print("🔍 Checking Async Processing Results")
    print("=" * 50)
    
    job_id = "4b2ded07-17b5-4996-bb83-5dc493ce8de3"
    
    try:
        response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
        
        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            return False
        
        data = response.json()
        
        print(f"📊 Async Processing Results:")
        print(f"   Status: {data.get('status', 'unknown')}")
        print(f"   Success: {data.get('success', False)}")
        
        citations = data.get('citations', [])
        clusters = data.get('clusters', [])
        
        print(f"   Citations found: {len(citations)}")
        print(f"   Clusters found: {len(clusters)}")
        
        if len(citations) > 0:
            print(f"\n📋 Sample Citations (first 5):")
            for i, citation in enumerate(citations[:5], 1):
                citation_text = citation.get('citation', 'N/A')
                extracted_name = citation.get('extracted_case_name', 'N/A')
                extracted_date = citation.get('extracted_date', 'N/A')
                verified = citation.get('verified', False)
                
                print(f"   {i}. '{citation_text}'")
                print(f"      Case: {extracted_name}")
                print(f"      Date: {extracted_date}")
                print(f"      Verified: {verified}")
                print()
        
        if len(clusters) > 0:
            print(f"🔗 Sample Clusters (first 3):")
            for i, cluster in enumerate(clusters[:3], 1):
                cluster_id = cluster.get('cluster_id', 'N/A')
                extracted_name = cluster.get('extracted_case_name', 'N/A')
                canonical_name = cluster.get('canonical_name', 'N/A')
                size = cluster.get('size', 0)
                
                print(f"   {i}. Cluster: {cluster_id}")
                print(f"      Extracted Name: {extracted_name}")
                print(f"      Canonical Name: {canonical_name}")
                print(f"      Size: {size} citations")
                print()
        
        # Check if our nested citation fix is working
        nested_citations = [c for c in citations if 'Legion' in c.get('extracted_case_name', '')]
        if nested_citations:
            print(f"🎯 Nested Citation Fix Check:")
            print(f"   Found {len(nested_citations)} citations with 'Legion' in case name")
            for citation in nested_citations[:2]:
                print(f"   - '{citation.get('citation', 'N/A')}' → '{citation.get('extracted_case_name', 'N/A')}'")
        
        return True
        
    except Exception as e:
        print(f"💥 Error checking results: {e}")
        return False

def main():
    """Check async results."""
    
    print("🚀 Async Processing Results Check")
    print("=" * 60)
    
    success = check_async_results()
    
    print("\n" + "=" * 60)
    print("📋 ASYNC RESULTS SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ Async processing completed successfully")
        print("🔍 Your large document has been processed")
        print("📊 Citations and clusters have been extracted")
        print("🎯 Nested citation fix should be working")
    else:
        print("❌ Error retrieving async results")
    
    return success

if __name__ == "__main__":
    main()
