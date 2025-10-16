#!/usr/bin/env python
"""Find ALL Flying T Ranch citations"""
import requests
import json

task_id = "debug-test-logging"
url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"

response = requests.get(url, timeout=10)
data = response.json()

print("=" * 80)
print("ALL CITATIONS MENTIONING 'Flying T' OR 'Stillaguamish'")
print("=" * 80)

flying_t_citations = []
for cit in data.get('citations', []):
    extracted = cit.get('extracted_case_name', '')
    if 'flying t' in extracted.lower() or 'stillaguamish' in extracted.lower():
        flying_t_citations.append(cit)

print(f"\nFound {len(flying_t_citations)} citations:\n")

for i, cit in enumerate(flying_t_citations, 1):
    print(f"{i}. {cit.get('citation', 'N/A')}")
    print(f"   Extracted: {cit.get('extracted_case_name', 'N/A')}")
    print(f"   Year: {cit.get('extracted_date', 'N/A')}")
    print(f"   Cluster: {cit.get('cluster_id', 'None')}")
    print(f"   Verified: {'✅' if cit.get('verified') else '❌'}")
    print()
