#!/usr/bin/env python3
"""
Test the current issues:
1. Progress bar not working in sync
2. Extraction issue (canonical names showing N/A)
"""

import requests
import time
import json

def test_progress_bar_sync():
    """Test if progress bar is working in sync mode."""
    
    print("📊 Testing Progress Bar in Sync Mode")
    print("=" * 50)
    
    # Test the processing_progress endpoint
    try:
        print("🔍 Testing processing_progress endpoint...")
        for i in range(5):
            response = requests.get(
                "http://localhost:8080/casestrainer/api/processing_progress",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Request {i+1}: {data.get('current_step')} - {data.get('total_progress')}%")
            else:
                print(f"   Request {i+1}: Error {response.status_code}")
            
            time.sleep(0.2)
        
        # Test actual sync processing
        print(f"\n🔄 Testing sync processing with progress...")
        test_text = "The case State v. Johnson, 160 Wn.2d 500 (2007) is important."
        
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"text": test_text, "type": "text"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            processing_mode = data.get('metadata', {}).get('processing_mode')
            progress_data = data.get('progress_data')
            
            print(f"   Processing mode: {processing_mode}")
            print(f"   Progress data present: {progress_data is not None}")
            
            if processing_mode == 'immediate':
                print(f"   ✅ Sync processing detected")
                if progress_data:
                    print(f"   ✅ Progress data included")
                    return True
                else:
                    print(f"   ❌ No progress data in sync response")
                    return False
            else:
                print(f"   ⚠️ Not sync processing: {processing_mode}")
                return False
        else:
            print(f"   ❌ API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Progress bar test failed: {e}")
        return False

def test_canonical_names_extraction():
    """Test canonical names extraction for the specific case mentioned."""
    
    print(f"\n🔍 Testing Canonical Names Extraction")
    print("=" * 50)
    
    # Test with the specific case mentioned: State v. M.Y.G.
    test_cases = [
        {
            "name": "State v. M.Y.G. 2022",
            "text": "The case State v. M.Y.G., 199 Wash.2d 528, 509 P.3d 818 (2022) is relevant."
        },
        {
            "name": "State v. M.Y.G. 1991", 
            "text": "See also State v. M.Y.G., 116 Wash.2d 1, 802 P.2d 784 (1991) for precedent."
        },
        {
            "name": "Well-known case (should verify)",
            "text": "Brown v. Board of Education, 347 U.S. 483 (1954) is landmark."
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json={"text": test_case['text'], "type": "text"},
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"   ❌ API Error: {response.status_code}")
                continue
            
            data = response.json()
            processing_mode = data.get('metadata', {}).get('processing_mode')
            
            # Handle async processing if needed
            if processing_mode == 'queued':
                job_id = data.get('metadata', {}).get('job_id')
                if job_id:
                    print(f"   ⏳ Async processing: {job_id}")
                    for attempt in range(15):
                        time.sleep(2)
                        status_response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get('status') == 'completed':
                                data = status_data
                                break
                    else:
                        print(f"   ❌ Async timeout")
                        continue
            
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            
            print(f"   📊 Results:")
            print(f"     Citations: {len(citations)}")
            print(f"     Clusters: {len(clusters)}")
            
            # Check cluster canonical data
            canonical_names_found = 0
            verified_clusters = 0
            
            for i, cluster in enumerate(clusters, 1):
                canonical_name = cluster.get('canonical_name')
                canonical_date = cluster.get('canonical_date')
                extracted_case_name = cluster.get('extracted_case_name')
                
                # Check if any citations in cluster are verified
                citation_objects = cluster.get('citation_objects', [])
                verified_in_cluster = [c for c in citation_objects if c.get('verified')]
                
                print(f"     Cluster {i}:")
                print(f"       Extracted name: '{extracted_case_name}'")
                print(f"       Canonical name: '{canonical_name}'")
                print(f"       Canonical date: '{canonical_date}'")
                print(f"       Verified citations: {len(verified_in_cluster)}/{len(citation_objects)}")
                
                if len(verified_in_cluster) > 0:
                    verified_clusters += 1
                    
                    if canonical_name and canonical_name != 'N/A':
                        canonical_names_found += 1
                        print(f"       ✅ Has canonical name")
                    else:
                        print(f"       ❌ Missing canonical name (would show N/A)")
                else:
                    print(f"       ⚠️ No verified citations (expected to show N/A)")
            
            result = {
                "name": test_case['name'],
                "clusters": len(clusters),
                "verified_clusters": verified_clusters,
                "canonical_names_found": canonical_names_found,
                "success": canonical_names_found > 0 if verified_clusters > 0 else True
            }
            
            results.append(result)
            
        except Exception as e:
            print(f"   💥 Exception: {e}")
            results.append({"name": test_case['name'], "success": False, "error": str(e)})
    
    # Summary
    print(f"\n📊 Canonical Names Test Summary:")
    for result in results:
        if result.get('error'):
            print(f"   ❌ {result['name']}: Error - {result['error']}")
        else:
            verified = result.get('verified_clusters', 0)
            canonical = result.get('canonical_names_found', 0)
            if verified > 0:
                status = "✅" if canonical > 0 else "❌"
                print(f"   {status} {result['name']}: {canonical}/{verified} verified clusters have canonical names")
            else:
                print(f"   ⚠️ {result['name']}: No verified clusters (N/A expected)")
    
    return any(r.get('success', False) for r in results)

def main():
    """Test both current issues."""
    
    print("🚀 Testing Current Issues")
    print("=" * 60)
    
    # Test both issues
    progress_ok = test_progress_bar_sync()
    canonical_ok = test_canonical_names_extraction()
    
    print("\n" + "=" * 60)
    print("📋 CURRENT ISSUES TEST RESULTS")
    print("=" * 60)
    
    print(f"1. Progress Bar in Sync Mode: {'✅ WORKING' if progress_ok else '❌ BROKEN'}")
    print(f"2. Canonical Names Extraction: {'✅ WORKING' if canonical_ok else '❌ BROKEN'}")
    
    if not progress_ok:
        print("\n🔧 Progress Bar Issue:")
        print("   - Check if /processing_progress endpoint is working")
        print("   - Verify frontend is polling the endpoint correctly")
        print("   - Check for JavaScript errors in browser console")
    
    if not canonical_ok:
        print("\n🔧 Canonical Names Issue:")
        print("   - Citations may not be getting verified")
        print("   - Verification services may be unavailable")
        print("   - Canonical data propagation may not be working")
    
    return progress_ok and canonical_ok

if __name__ == "__main__":
    main()
