import json

with open('24-2626_comprehensive_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find the Johnson cluster
for cluster in data['clusters']:
    if cluster['size'] > 1:
        print(f"Cluster: {cluster['case_name']}")
        print(f"Cluster ID: {cluster['cluster_id']}")
        print(f"Size: {cluster['size']}")
        print(f"Extracted case name: {cluster.get('extracted_case_name')}")
        print(f"Extracted date: {cluster.get('extracted_date')}")
        print()
        
        for cit in cluster['citation_details']:
            print(f"Citation: {cit['text']}")
            print(f"  Verified: {cit.get('verified')}")
            print(f"  Canonical name: {cit.get('canonical_name')}")
            print(f"  Canonical date: {cit.get('canonical_date')}")
            print(f"  Extracted name: {cit.get('extracted_case_name')}")
            print(f"  Extracted date: {cit.get('extracted_date')}")
            print(f"  Metadata: {cit.get('metadata')}")
            print()
