import requests
import json

print("Uploading PDF to CaseStrainer API...")

with open(r'D:\dev\casestrainer\1034300.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:5000/casestrainer/api/analyze',
        files=files,
        timeout=180
    )

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    
    # Save full response
    with open('test_result.json', 'w') as out:
        json.dump(result, out, indent=2)
    
    # Print summary
    clusters = result.get('clusters', [])
    citations = result.get('citations', [])
    
    print(f"\n✅ SUCCESS!")
    print(f"Total Citations: {len(citations)}")
    print(f"Total Clusters: {len(clusters)}")
    
    # Check canonical data
    clusters_with_canonical = 0
    for cluster in clusters:
        if cluster.get('canonical_name'):
            clusters_with_canonical += 1
            print(f"\n✅ Cluster has canonical data:")
            print(f"   Name: {cluster.get('canonical_name')}")
            print(f"   Date: {cluster.get('canonical_date')}")
            print(f"   Source: {cluster.get('verification_source')}")
    
    print(f"\n📊 Summary: {clusters_with_canonical}/{len(clusters)} clusters have canonical data")
    
    if clusters_with_canonical > 3:
        print("🎉 FIX WORKED! More than 3 clusters have canonical data!")
    elif clusters_with_canonical == 3:
        print("⚠️  Still only 3 clusters - fix may not be applied yet")
    else:
        print("❌ No clusters have canonical data")
        
else:
    print(f"❌ Error: {response.text}")
