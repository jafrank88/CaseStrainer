import json

with open('24-2626_comprehensive_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

multi = [c for c in data['clusters'] if c['size'] > 1]

print(f"Multi-citation clusters: {len(multi)}")
print()

for c in multi:
    print(f"Cluster: {c['case_name']} ({c['size']} citations)")
    for cit in c['citation_details']:
        verified = "✓" if cit.get('verified') else "✗"
        canonical = cit.get('canonical_name', 'N/A')
        extracted = cit.get('extracted_case_name', 'N/A')
        year = cit.get('extracted_date', 'N/A')
        print(f"  {verified} {cit['text']:20} | Extracted: {extracted[:50]:50} ({year}) | Canonical: {canonical[:50] if canonical else 'N/A'}")
    print()
