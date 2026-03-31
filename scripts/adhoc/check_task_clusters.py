import requests
import json

# Check the most recent task that completed
task_id = "290fd6f0-b111-4db9-98ba-0fc059f2d491"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Citations: {len(data.get('citations', []))}")
        print(f"Clusters: {len(data.get('clusters', []))}")
        
        # Check verified citations
        citations = data.get('citations', [])
        verified_citations = [c for c in citations if c.get('verified', False)]
        print(f"Verified citations: {len(verified_citations)}")
        
        # Check clusters with verified citations
        clusters = data.get('clusters', [])
        clusters_with_verified = 0
        for cluster in clusters:
            cluster_cits = cluster.get('citations', [])
            if any(cit.get('verified', False) for cit in cluster_cits):
                clusters_with_verified += 1
        
        print(f"Clusters with verified citations: {clusters_with_verified}")
        
        # Show sample
        if verified_citations:
            print(f"\nSample verified citation:")
            cit = verified_citations[0]
            print(f"  Citation: {cit.get('citation')}")
            print(f"  Case name: {cit.get('canonical_name') or cit.get('extracted_case_name')}")
            print(f"  Verified: {cit.get('verified')}")
        
        if clusters_with_verified > 0:
            print(f"\nSample cluster with verified citations:")
            for cluster in clusters:
                cluster_cits = cluster.get('citations', [])
                verified_in_cluster = [c for c in cluster_cits if c.get('verified', False)]
                if verified_in_cluster:
                    print(f"  Cluster: {cluster.get('case_name')}")
                    print(f"  Verified citations: {len(verified_in_cluster)}")
                    print(f"  Total citations: {len(cluster_cits)}")
                    break
        else:
            print(f"\n❌ No clusters contain verified citations")
            
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
