"""Test why specific citations are still contaminated"""
import json

# Load results
with open('24-2626_comprehensive_results.json', 'r') as f:
    data = json.load(f)

# Find the 3 contaminated citations
contam_cits = ['129 F.4th 1196', '511 U.S. 863', '106 P.3d 958']

print("=" * 80)
print("ANALYZING CONTAMINATED CITATIONS")
print("=" * 80)

for cit_text in contam_cits:
    citation = next((c for c in data['citations'] if c['citation'] == cit_text), None)
    if citation:
        print(f"\n📍 Citation: {cit_text}")
        print(f"   Method: {citation.get('method', 'unknown')}")
        print(f"   Extracted: '{citation.get('extracted_case_name', 'N/A')}'")
        print(f"   Cluster: '{citation.get('cluster_case_name', 'N/A')}'")
        print(f"   Canonical: '{citation.get('canonical_name', 'N/A')}'")
        print(f"   Context: {citation.get('context', '')[:100]}")
    else:
        print(f"\n❌ Citation {cit_text} not found in results")

print("\n" + "=" * 80)
print("THEORY: These may be coming from eyecite or clustering phase")
print("=" * 80)
