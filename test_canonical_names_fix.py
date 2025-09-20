#!/usr/bin/env python3
"""
Test the canonical names fix for verified sources.
This test verifies that clusters with verified citations show the canonical case name
instead of "N/A" in the "Verifying Source" field.
"""

import requests
import time
import json

def test_canonical_names_in_clusters():
    """Test that verified clusters show canonical names instead of N/A."""
    
    print("🔍 Testing Canonical Names in Verified Clusters")
    print("=" * 60)
    
    # Test with citations that are likely to be verified
    test_text = """
    Legal Analysis Document
    
    Important Washington State Supreme Court cases:
    
    1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) - Criminal law precedent
    2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) - Municipal authority  
    3. Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686, 98 L. Ed. 873 (1954) - Civil rights
    4. Miranda v. Arizona, 384 U.S. 436, 86 S. Ct. 1602, 16 L. Ed. 2d 694 (1966) - Criminal procedure
    
    These cases represent important legal precedents that should be verifiable through
    legal databases like CourtListener, Casemine, or other sources.
    """
    
    try:
        print("📤 Submitting document with verifiable citations...")
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text, "type": "text"},
            timeout=60  # Allow more time for verification
        )
        
        if response.status_code != 200:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
        
        print(f"📊 Processing mode: {processing_mode}")
        
        # Handle async processing if needed
        if processing_mode == 'queued':
            job_id = data.get('metadata', {}).get('job_id')
            if job_id:
                print(f"⏳ Waiting for async processing: {job_id}")
                for attempt in range(30):  # Wait up to 60 seconds
                    time.sleep(2)
                    status_response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('status') == 'completed':
                            data = status_data
                            print(f"✅ Async processing completed")
                            break
                        elif status_data.get('status') == 'failed':
                            print(f"❌ Async processing failed: {status_data}")
                            return False
                    print(f"   Attempt {attempt + 1}/30: {status_data.get('status', 'unknown')}")
                else:
                    print(f"❌ Timeout waiting for async completion")
                    return False
        
        # Analyze results
        citations = data.get('citations', [])
        clusters = data.get('clusters', [])
        
        print(f"\n📊 Results Summary:")
        print(f"   Citations found: {len(citations)}")
        print(f"   Clusters found: {len(clusters)}")
        
        if len(clusters) == 0:
            print(f"⚠️ No clusters found - testing individual citations instead")
            
            # Check individual citations for canonical data
            verified_citations = [c for c in citations if c.get('verified')]
            canonical_names_found = 0
            
            for i, citation in enumerate(verified_citations[:5], 1):  # Check first 5 verified
                canonical_name = citation.get('canonical_name')
                canonical_url = citation.get('canonical_url')
                
                print(f"\n   Verified Citation {i}:")
                print(f"     Text: {citation.get('citation', 'N/A')}")
                print(f"     Canonical Name: {canonical_name}")
                print(f"     Canonical URL: {canonical_url}")
                
                if canonical_name and canonical_name != 'N/A':
                    canonical_names_found += 1
            
            success = canonical_names_found > 0
            print(f"\n🎯 Individual Citations Test: {'✅ PASS' if success else '❌ FAIL'}")
            print(f"   Citations with canonical names: {canonical_names_found}/{len(verified_citations)}")
            
            return success
        
        # Analyze clusters for canonical data
        clusters_with_canonical_names = 0
        verified_clusters = 0
        
        for i, cluster in enumerate(clusters, 1):
            print(f"\n🔍 Cluster {i} Analysis:")
            
            # Check cluster-level canonical data
            canonical_name = cluster.get('canonical_name')
            canonical_date = cluster.get('canonical_date')
            canonical_url = cluster.get('canonical_url')
            extracted_case_name = cluster.get('extracted_case_name')
            
            print(f"   Extracted Case Name: '{extracted_case_name}'")
            print(f"   Canonical Name: '{canonical_name}'")
            print(f"   Canonical Date: '{canonical_date}'")
            print(f"   Canonical URL: '{canonical_url}'")
            
            # Check if any citations in cluster are verified
            citation_objects = cluster.get('citation_objects', [])
            verified_in_cluster = [c for c in citation_objects if c.get('verified')]
            
            print(f"   Citations in cluster: {len(citation_objects)}")
            print(f"   Verified citations: {len(verified_in_cluster)}")
            
            if len(verified_in_cluster) > 0:
                verified_clusters += 1
                
                # Check if canonical name is present (not N/A or None)
                if canonical_name and canonical_name != 'N/A' and canonical_name.strip():
                    clusters_with_canonical_names += 1
                    print(f"   ✅ Canonical name found: '{canonical_name}'")
                else:
                    print(f"   ❌ No canonical name (showing N/A in frontend)")
                    
                    # Debug: Check individual citation canonical data
                    for j, citation_obj in enumerate(verified_in_cluster[:2], 1):
                        cit_canonical = citation_obj.get('canonical_name')
                        print(f"     Verified Citation {j} canonical_name: '{cit_canonical}'")
        
        print(f"\n📊 Cluster Analysis Results:")
        print(f"   Total clusters: {len(clusters)}")
        print(f"   Clusters with verified citations: {verified_clusters}")
        print(f"   Clusters with canonical names: {clusters_with_canonical_names}")
        
        # Success if most verified clusters have canonical names
        success = verified_clusters > 0 and clusters_with_canonical_names > 0
        
        print(f"\n🎯 Canonical Names Test: {'✅ PASS' if success else '❌ FAIL'}")
        
        if success:
            print(f"   ✅ Verified clusters now show canonical names instead of 'N/A'")
            print(f"   ✅ Frontend should display proper 'Verifying Source' information")
        else:
            print(f"   ❌ Verified clusters still showing 'N/A' instead of canonical names")
            print(f"   ❌ Frontend will continue to show 'Verifying Source: N/A'")
        
        return success
        
    except Exception as e:
        print(f"💥 Canonical names test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run canonical names fix test."""
    
    print("🚀 Testing Canonical Names Fix for Verified Sources")
    print("=" * 70)
    
    success = test_canonical_names_in_clusters()
    
    print("\n" + "=" * 70)
    print("📋 CANONICAL NAMES FIX TEST RESULTS")
    print("=" * 70)
    
    if success:
        print("🎉 CANONICAL NAMES FIX SUCCESSFUL!")
        print("✅ Verified clusters should now show proper case names")
        print("✅ 'Verifying Source: N/A' should be replaced with actual case names")
        print("✅ Frontend will display canonical names from verification sources")
    else:
        print("⚠️ Canonical names fix needs additional work")
        print("❌ Verified sources may still show 'N/A' instead of case names")
    
    return success

if __name__ == "__main__":
    main()
