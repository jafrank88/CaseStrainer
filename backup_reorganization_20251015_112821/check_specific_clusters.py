"""Check the specific clusters flagged as false"""
import json

with open('24-2626_comprehensive_results.json', 'r') as f:
    data = json.load(f)

# Find "Will v. Hallock" and "La Liberte v. Reid" clusters
target_clusters = []
for cluster in data['clusters']:
    case_name = cluster.get('case_name', '')
    if 'Will v. Hallock' in case_name or 'La Liberte v. Reid' in case_name:
        target_clusters.append(cluster)

print("=" * 80)
print("ANALYZING FLAGGED CLUSTERS")
print("=" * 80)

for cluster in target_clusters:
    case_name = cluster.get('case_name', 'N/A')
    citations = cluster.get('citations', [])
    
    print(f"\n📍 Cluster: {case_name}")
    print(f"   Citations ({len(citations)}):")
    
    for cit in citations:
        cit_text = cit.get('text', 'N/A')
        parts = cit_text.strip().split()
        if len(parts) >= 2:
            volume = parts[0]
            reporter = ' '.join([p for p in parts[1:] if not p.isdigit()])
            print(f"      {cit_text:30} | volume: {volume:5} | reporter: {reporter}")
        else:
            print(f"      {cit_text:30} | UNPARSEABLE")

print("\n" + "=" * 80)
