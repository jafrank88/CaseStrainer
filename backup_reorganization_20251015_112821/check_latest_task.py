import requests
import json

task_id = "19cc3f99-7e48-4f52-bfd9-3e55cbf460bc"
url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"

response = requests.get(url)
data = response.json()

print(f"Response keys: {list(data.keys())}")
print(f"Status: {data.get('status')}")
print(f"Citations: {len(data.get('citations', []))}")
print(f"Clusters: {len(data.get('clusters', []))}")

if len(data.get('citations', [])) > 0:
    # Check contamination
    contaminated = []
    for cite in data['citations']:
        name = (cite.get('extracted_case_name', '') or '').lower()
        if any(word in name for word in ['gopher', 'melone', 'thakore']):
            contaminated.append(cite)
    
    print(f"\n📊 Contamination AFTER FIX: {len(contaminated)}/{len(data['citations'])} ({len(contaminated)/len(data['citations'])*100:.1f}%)")
    
    if contaminated:
        print("\n❌ Still contaminated (fix didn't work):")
        for cite in contaminated[:10]:
            print(f"   {cite['citation']:30} -> {cite.get('extracted_case_name', '')[:60]}")
    else:
        print("\n✅ NO CONTAMINATION! Fix is working!")
else:
    print("\n⚠️  No citations found")
