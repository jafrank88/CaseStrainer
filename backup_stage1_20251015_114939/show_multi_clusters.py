"""Show all multi-citation clusters"""
import json

with open('24-2626_comprehensive_results.json', 'r') as f:
    data = json.load(f)

multi = [c for c in data['clusters'] if len(c.get('citations', [])) > 1]

print(f"Found {len(multi)} multi-citation clusters:\n")

for i, cluster in enumerate(multi, 1):
    case_name = cluster.get('case_name', 'N/A')
    citations = cluster.get('citations', [])
    print(f"{i}. {case_name} ({len(citations)} citations):")
    for cit in citations:
        print(f"   - {cit.get('citation', 'N/A')}")
    print()
