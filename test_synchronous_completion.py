#!/usr/bin/env python3
"""
Test to verify synchronous completion waits for full verification
and includes verified citations in clusters
"""

import requests
import time
import json

def test_synchronous_completion():
    """Test that async processing now waits for full verification"""
    
    print("🔍 TESTING SYNCHRONOUS COMPLETION WITH VERIFICATION")
    print("=" * 60)
    
    # Use test document with known verifiable citations
    test_text = """
    City of Bellevue v. Lorang, 114 Wn. App. 245, 57 P.3d 273 (2002).
    Greenhalgh v. Dep't of Corr, 90 Wn. App. 533, 954 P.2d 290 (1998).
    179 Wn.2d 737 (2014). 317 P.3d 1037 (2014).
    171 Wn.2d 820 (2011). 256 P.3d 1150 (2011).
    131 Wn. App. 756 (2006). 129 P.3d 300 (2006).
    146 Wn.2d 1 (2002). 43 P.3d 4 (2002).
    119 Wn. App. 886 (2004). 83 P.3d 433 (2004).
    145 Wn. App. 118 (2008). 186 P.3d 357 (2008).
    120 Wn. App. 175 (2004). 84 P.3d 927 (2004).
    140 Wn.2d 19 (2000). 992 P.2d 496 (2000).
    129 Wn.2d 652 (1996). 921 P.2d 473 (1996).
    116 Wn.2d 342 (1991). 804 P.2d 24 (1991).
    180 Wn. App. 876 (2014). 324 P.3d 771 (2014).
    182 Wn.2d 55 (2014).
    Durland v. San Juan County, 340 P.3d 191 (2014).
    408 U. S. 564 (1972).
    161 F.3d 584 (1998).
    425 F.3d 1158 (2005).
    """ * 15  # Make it large enough to trigger async
    
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    data = {
        'type': 'text',
        'text': test_text,
        'enable_verification': True
    }
    
    print(f"📋 Making API call...")
    print(f"Text length: {len(test_text)} characters")
    print(f"Expected behavior: Wait for full verification before returning")
    
    try:
        response = requests.post(api_url, json=data, timeout=60)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            if task_id:
                print(f"\n✅ Task ID: {task_id}")
                print(f"🔄 Monitoring for synchronous completion...")
                
                progress_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
                
                start_time = time.time()
                final_result = None
                
                # Monitor progress
                for i in range(30):  # Check for 60 seconds
                    try:
                        progress_response = requests.get(progress_url, timeout=5)
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            status = progress_data.get('status')
                            progress = progress_data.get('progress_percent', 0)
                            citations = progress_data.get('citations', [])
                            clusters = progress_data.get('clusters', [])
                            
                            elapsed = time.time() - start_time
                            print(f"Attempt {i+1} ({elapsed:.1f}s): Status={status}, Progress={progress}%, Citations={len(citations)}, Clusters={len(clusters)}")
                            
                            if status == 'completed':
                                print(f"\n🎉 TASK COMPLETED!")
                                final_result = progress_data
                                break
                            elif status == 'failed':
                                print(f"❌ TASK FAILED: {progress_data.get('error')}")
                                break
                            elif status == 'processing' and progress == 0:
                                print(f"  ⏳ Still waiting - no early completion (expected)")
                                
                    except Exception as e:
                        print(f"Attempt {i+1}: Error polling: {e}")
                    
                    time.sleep(2)
                else:
                    print("⏰ Task still not completed after 60 seconds")
                
                # Analyze final result
                if final_result:
                    print(f"\n📊 FINAL RESULT ANALYSIS:")
                    
                    citations = final_result.get('citations', [])
                    clusters = final_result.get('clusters', [])
                    
                    print(f"Total citations: {len(citations)}")
                    print(f"Total clusters: {len(clusters)}")
                    
                    # Check verification status
                    verified_citations = [c for c in citations if c.get('verified', False)]
                    print(f"Verified citations: {len(verified_citations)}")
                    
                    # Check clusters with verified citations
                    clusters_with_verified = 0
                    verified_citations_in_clusters = 0
                    
                    for cluster in clusters:
                        cluster_cits = cluster.get('citations', [])
                        cluster_verified = [c for c in cluster_cits if c.get('verified', False)]
                        if cluster_verified:
                            clusters_with_verified += 1
                            verified_citations_in_clusters += len(cluster_verified)
                    
                    print(f"Clusters with verified citations: {clusters_with_verified}")
                    print(f"Verified citations found in clusters: {verified_citations_in_clusters}")
                    
                    # Check if verified citations appear in clusters
                    if verified_citations and verified_citations_in_clusters > 0:
                        print(f"\n✅ SUCCESS: Verified citations appear in clusters!")
                        print(f"  - {len(verified_citations)} verified citations total")
                        print(f"  - {verified_citations_in_clusters} verified citations in clusters")
                        
                        # Show sample verified citations in clusters
                        print(f"\n📋 Sample verified citations in clusters:")
                        count = 0
                        for cluster in clusters:
                            cluster_cits = cluster.get('citations', [])
                            for cit in cluster_cits:
                                if cit.get('verified', False) and count < 3:
                                    cit_text = cit.get('citation', 'Unknown')
                                    case_name = cit.get('canonical_name') or cit.get('extracted_case_name', 'N/A')
                                    print(f"  ✅ {cit_text} - {case_name}")
                                    count += 1
                    elif verified_citations:
                        print(f"\n⚠️  ISSUE: {len(verified_citations)} verified citations found but none in clusters")
                        print(f"This indicates clusters are not including verified citation data")
                    else:
                        print(f"\n⚠️  No verified citations found - verification may have failed")
                        
            else:
                print("❌ No task ID returned")
        else:
            print(f"❌ API call failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_synchronous_completion()
