import requests
import json

# Upload the PDF file
url = "http://localhost:5000/casestrainer/api/analyze"
files = {'file': open('D:/dev/casestrainer/motion.pdf', 'rb')}
data = {'force_mode': 'sync'}

print("Uploading motion.pdf to backend...")
response = requests.post(url, files=files, data=data, timeout=300)

if response.status_code == 200:
    result = response.json()
    
    # Check for WL citations
    print("\n=== WL Citations ===")
    for cit in result.get('citations', []):
        citation_text = cit.get('citation', '')
        if 'WL' in citation_text:
            print(f"\nCitation: {citation_text}")
            print(f"  Verified: {cit.get('verified')}")
            print(f"  Status: {cit.get('verification_status')}")
            print(f"  Error: {cit.get('error')}")
            print(f"  Source: {cit.get('source')}")
    
    # Check for Id. citations in clusters
    print("\n\n=== Id. Citations in Clusters ===")
    for cluster in result.get('clusters', []):
        for cit in cluster.get('citations', []):
            citation_text = cit.get('citation', '')
            if citation_text and 'Id.' in citation_text:
                print(f"\nFound Id. in cluster {cluster.get('cluster_id')}: {citation_text}")
    
    # Check cluster count
    print(f"\n\n=== Summary ===")
    print(f"Total citations: {len(result.get('citations', []))}")
    print(f"Total clusters: {len(result.get('clusters', []))}")
    print(f"Verified: {sum(1 for c in result.get('citations', []) if c.get('verified'))}")
else:
    print(f"Error: {response.status_code}")
