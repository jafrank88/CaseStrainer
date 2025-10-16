"""Show cluster data structure"""
import json

with open('24-2626_comprehensive_results.json', 'r') as f:
    data = json.load(f)

multi = [c for c in data['clusters'] if len(c.get('citations', [])) > 1]

if multi:
    print("Sample cluster structure:")
    print(json.dumps(multi[0], indent=2)[:1000])
    print("\n...")
    print("\nSample citation from cluster:")
    if multi[0].get('citations'):
        cit = multi[0]['citations'][0]
        print(json.dumps(cit, indent=2)[:500])
