import json

with open('motion_test_semicolon_fix.json', 'r') as f:
    data = json.load(f)

print("Checking if semicolon fix resolved the issue...")
print("=" * 80)

# Find all occurrences of "2024 WL 1232082"
wl_citations = []
for cit in data.get('citations', []):
    citation_text = cit.get('citation', '')
    if '2024 WL 1232082' in citation_text:
        wl_citations.append({
            'citation': citation_text,
            'position': f"{cit.get('start_index')}-{cit.get('end_index')}",
            'extracted_case_name': cit.get('extracted_case_name'),
            'cluster_id': cit.get('cluster_id'),
        })

print(f"Found {len(wl_citations)} occurrences of '2024 WL 1232082':\n")

for i, cit in enumerate(wl_citations, 1):
    print(f"Occurrence {i}:")
    print(f"  Citation: {cit['citation']}")
    print(f"  Position: {cit['position']}")
    print(f"  Extracted name: {cit['extracted_case_name']}")
    print(f"  Cluster ID: {cit['cluster_id']}")
    
    # Check if it's correct
    if 'Doe v. Teachers Council' in cit['extracted_case_name']:
        print(f"  ✅ CORRECT - Extracted 'Doe v. Teachers Council'")
    elif 'Schiller' in cit['extracted_case_name']:
        print(f"  ❌ WRONG - Still extracting 'Schiller' (contamination)")
    else:
        print(f"  ⚠️  UNEXPECTED - Different case name")
    print()

# Check if they're in the same cluster
if len(wl_citations) == 2:
    if wl_citations[0]['cluster_id'] == wl_citations[1]['cluster_id']:
        print("❌ PROBLEM: Both occurrences in same cluster")
    else:
        print("✅ GOOD: Occurrences in different clusters")
        
# Also check the Schiller/2006 WL citation
print("\n" + "=" * 80)
print("Checking Schiller v. City of New York citations:\n")

schiller_citations = []
for cit in data.get('citations', []):
    extracted_name = cit.get('extracted_case_name', '')
    if 'Schiller' in extracted_name:
        schiller_citations.append({
            'citation': cit.get('citation'),
            'extracted_case_name': extracted_name,
            'cluster_id': cit.get('cluster_id'),
        })

for cit in schiller_citations:
    print(f"Citation: {cit['citation']}")
    print(f"  Extracted name: {cit['extracted_case_name']}")
    print(f"  Cluster ID: {cit['cluster_id']}")
    print()
