import requests
import json

task_id = "56702e6e-ee68-43e7-bf50-03e4ca1b9f3a"
url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"

response = requests.get(url)
data = response.json()

print(f"Response keys: {list(data.keys())}")
print(f"Status: {data.get('status')}")
print(f"Citations: {len(data.get('citations', []))}")
print(f"Clusters: {len(data.get('clusters', []))}")

if len(data.get('citations', [])) > 0:
    print("\nFirst 3 citations:")
    for i, cite in enumerate(data['citations'][:3], 1):
        print(f"{i}. {cite.get('citation', '')}: {cite.get('extracted_case_name', 'N/A')[:60]}")
    
    # Check contamination
    contaminated = []
    for cite in data['citations']:
        name = (cite.get('extracted_case_name', '') or '').lower()
        if any(word in name for word in ['gopher', 'melone', 'thakore']):
            contaminated.append(cite)
    
    print(f"\n📊 Contamination: {len(contaminated)}/{len(data['citations'])} ({len(contaminated)/len(data['citations'])*100:.1f}%)")
    
    if contaminated:
        print("\nFirst 5 contaminated:")
        for cite in contaminated[:5]:
            print(f"   {cite['citation']:30} -> {cite.get('extracted_case_name', '')[:60]}")

# Save to file for inspection
with open('task_result_full.json', 'w') as f:
    json.dump(data, f, indent=2)
print("\nFull result saved to task_result_full.json")
