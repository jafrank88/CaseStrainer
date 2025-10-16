"""Test what CourtListener API returns for 199 Wn.2d 528"""

import requests
import json

citation = "199 Wn.2d 528"

url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
payload = {"text": citation}

print(f"=== TESTING API FOR: {citation} ===\n")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}\n")
    
    data = response.json()
    print(f"Response Structure: {type(data)}\n")
    
    if isinstance(data, list) and len(data) > 0:
        first_result = data[0]
        print(f"First Result Keys: {list(first_result.keys())}\n")
        
        status = first_result.get('status', 200)
        error_msg = first_result.get('error_message')
        clusters = first_result.get('clusters', [])
        
        print(f"Status: {status}")
        print(f"Error Message: {error_msg}")
        print(f"Number of Clusters: {len(clusters)}\n")
        
        if clusters:
            print("=== CLUSTERS ===")
            for i, cluster in enumerate(clusters):
                case_name = cluster.get('case_name', 'N/A')
                date_filed = cluster.get('date_filed', 'N/A')
                absolute_url = cluster.get('absolute_url', 'N/A')
                
                print(f"\nCluster {i+1}:")
                print(f"  Case Name: {case_name}")
                print(f"  Date Filed: {date_filed}")
                print(f"  URL: https://www.courtlistener.com{absolute_url}")
                
                # Check citations in this cluster
                citations = cluster.get('sub_opinions', [{}])[0].get('citations', []) if cluster.get('sub_opinions') else []
                print(f"  Citations in cluster: {len(citations)}")
                for cit in citations[:5]:  # First 5
                    print(f"    - {cit}")
        else:
            print("No clusters returned")
    else:
        print(f"Unexpected response format: {json.dumps(data, indent=2)[:500]}")
        
except Exception as e:
    print(f"ERROR: {e}")


