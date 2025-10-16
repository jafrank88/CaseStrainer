"""Final contamination test - check if filter is working"""
import requests

task_id = "99006d29-4aa9-400c-a30d-89e693cd2910"
url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"

response = requests.get(url)
data = response.json()

citations = data.get('citations', [])
print(f"✅ Citations: {len(citations)}")
print(f"✅ Clusters: {len(data.get('clusters', []))}")

# Check contamination
contaminated = []
for cite in citations:
    name = (cite.get('extracted_case_name', '') or '').lower()
    if any(word in name for word in ['gopher', 'melone', 'thakore']):
        contaminated.append(cite)

contamination_rate = len(contaminated) / len(citations) * 100 if citations else 0

print(f"\n📊 CONTAMINATION RESULT:")
if len(contaminated) == 0:
    print(f"   ✅ ✅ ✅ ZERO CONTAMINATION! Filter is WORKING! ✅ ✅ ✅")
else:
    print(f"   ❌ Still contaminated: {len(contaminated)}/{len(citations)} ({contamination_rate:.1f}%)")
    print(f"\n   Contaminated citations:")
    for cite in contaminated[:10]:
        print(f"      {cite['citation']:30} -> {cite.get('extracted_case_name', '')[:60]}")
