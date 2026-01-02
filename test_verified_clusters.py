#!/usr/bin/env python3
"""
Test to check if verified citations appear in clusters after background verification
"""

import requests
import time
import json

def test_verified_clusters():
    """Test if verified citations appear in clusters in final results"""
    
    print("🔍 TESTING VERIFIED CITATIONS IN CLUSTERS")
    print("=" * 50)
    
    # Use the same test document that produced verified citations
    test_text = """
    City of Bellevue v. Lorang, 114 Wn. App. 245, 57 P.3d 273 (2002).
    Greenhalgh v. Dep't of Corr, 90 Wn. App. 533, 954 P.2d 290 (1998).
    179 Wn.2d 737 (2014). 317 P.3d 1037 (2014).
    171 Wn.2d 820 (2011). 256 P.3d 1150 (2011).
    """ * 20  # Make it large enough to trigger async
    
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    data = {
        'type': 'text',
        'text': test_text,
        'enable_verification': True
    }
    
    print(f"📋 Making API call...")
    print(f"Text length: {len(test_text)} characters")
    
    try:
        response = requests.post(api_url, json=data, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            if task_id:
                print(f"\n✅ Task ID: {task_id}")
                print(f"🔄 Monitoring for background verification completion...")
                
                progress_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
                
                # Wait longer for background verification to complete
                for i in range(20):  # Check for 40 seconds
                    try:
                        progress_response = requests.get(progress_url, timeout=5)
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            status = progress_data.get('status')
                            progress = progress_data.get('progress_percent', 0)
                            citations = progress_data.get('citations', [])
                            clusters = progress_data.get('clusters', [])
                            
                            print(f"Attempt {i+1}: Status={status}, Progress={progress}%, Citations={len(citations)}, Clusters={len(clusters)}")
                            
                            if status == 'completed':
                                print(f"\n🎉 TASK COMPLETED!")
                                
                                # Check for verified citations
                                verified_citations = [c for c in citations if c.get('verified', False)]
                                print(f"📊 Verified citations: {len(verified_citations)}")
                                
                                # Check for verified clusters  
                                verified_clusters = []
                                for cluster in clusters:
                                    cluster_citations = cluster.get('citations', [])
                                    cluster_has_verified = any(
                                        cit.get('verified', False) if isinstance(cit, dict) else False 
                                        for cit in cluster_citations
                                    )
                                    if cluster_has_verified:
                                        verified_clusters.append(cluster)
                                
                                print(f"📊 Clusters with verified citations: {len(verified_clusters)}")
                                
                                # Show details
                                if verified_citations:
                                    print(f"\n✅ VERIFIED CITATIONS:")
                                    for i, cit in enumerate(verified_citations[:5]):
                                        cit_text = cit.get('citation', 'Unknown')
                                        case_name = cit.get('canonical_name') or cit.get('extracted_case_name', 'N/A')
                                        print(f"  {i+1}. {cit_text} - {case_name}")
                                
                                if verified_clusters:
                                    print(f"\n✅ VERIFIED CLUSTERS:")
                                    for i, cluster in enumerate(verified_clusters[:3]):
                                        cluster_name = cluster.get('case_name', 'N/A')
                                        cluster_citations = cluster.get('citations', [])
                                        verified_in_cluster = sum(1 for cit in cluster_citations if cit.get('verified', False))
                                        print(f"  {i+1}. {cluster_name} - {verified_in_cluster}/{len(cluster_citations)} verified")
                                else:
                                    print(f"\n❌ NO CLUSTERS WITH VERIFIED CITATIONS FOUND")
                                    print(f"This indicates verified citations are not being included in clusters")
                                
                                break
                            elif status == 'failed':
                                print(f"❌ TASK FAILED: {progress_data.get('error')}")
                                break
                                
                    except Exception as e:
                        print(f"Attempt {i+1}: Error polling: {e}")
                    
                    time.sleep(2)
                else:
                    print("⏰ Task still not completed after 40 seconds")
                    
            else:
                print("❌ No task ID returned")
        else:
            print(f"❌ API call failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_verified_clusters()
