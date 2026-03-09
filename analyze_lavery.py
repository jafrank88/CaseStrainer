"""Analyze Lavery v. Department results to identify all issues."""
import json

data = json.load(open('logs/reg_lavery_v5.json', 'r', encoding='utf-8'))
cits = data.get('citations', [])
clusters = data.get('clusters', [])

print(f"Total: {len(cits)} citations, {len(clusters)} clusters")
print()

# Issue 1: Truncated citations (Ill. 2 should be Ill. 2d, Ill. App. 3 should be Ill. App. 3d)
print("=== ISSUE: Truncated citations ===")
for c in cits:
    ct = c.get('citation', '')
    if ct.endswith(' 2') or ct.endswith(' 3') or ct.rstrip('0123456789').endswith(' 2') or ct.rstrip('0123456789').endswith(' 3'):
        # Check if it looks like a truncated Ill. 2d or Ill. App. 3d
        import re
        if re.search(r'Ill\.?\s+2\b', ct) or re.search(r'App\.?\s+3\b', ct) or re.search(r'A\.L\.R\.\s+2\b', ct):
            ecn = c.get('extracted_case_name', 'N/A')
            print(f"  TRUNC: '{ct}' ecn='{ecn}'")

print()

# Issue 2: N/A case names
print("=== ISSUE: N/A or missing case names ===")
na_cits = [(c.get('citation',''), c.get('extracted_case_name','')) for c in cits 
           if not c.get('extracted_case_name') or c.get('extracted_case_name') in ('N/A', 'N/a')]
for ct, ecn in na_cits:
    print(f"  N/A: '{ct[:70]}' ecn='{ecn}'")

print()

# Issue 3: Non-citation text extracted as citations
print("=== ISSUE: Non-citation text ===")
for c in cits:
    ct = c.get('citation', '')
    if 'Civil Rights Act' in ct or 'Illinois Constitution' in ct or len(ct) > 80:
        print(f"  NON-CIT: '{ct[:80]}'")

print()

# Issue 4: Duplicate clusters for same citation
print("=== ISSUE: Duplicate/split clusters ===")
from collections import Counter
# Count how many clusters reference 2023 IL App (1st) 220990
il_app_clusters = []
for cl in clusters:
    sdn = cl.get('submitted_display_name', '')
    for cc in cl.get('citations', []):
        if '220990' in cc.get('citation', ''):
            il_app_clusters.append(sdn)
            break
if len(il_app_clusters) > 1:
    print(f"  SPLIT: 2023 IL App (1st) 220990 appears in {len(il_app_clusters)} clusters:")
    for n in il_app_clusters:
        print(f"    - {n[:70]}")

print()

# Issue 5: Wrong case-citation pairings (e.g. 377 Ill. 255 in both Summy and Galpin)
print("=== ISSUE: Shared citations across clusters ===")
cit_to_clusters = {}
for cl in clusters:
    sdn = cl.get('submitted_display_name', '')
    for cc in cl.get('citations', []):
        ct = cc.get('citation', '')[:40]
        if ct not in cit_to_clusters:
            cit_to_clusters[ct] = []
        cit_to_clusters[ct].append(sdn)
for ct, cls_list in cit_to_clusters.items():
    if len(set(cls_list)) > 1:
        print(f"  SHARED: '{ct}' in: {[n[:40] for n in set(cls_list)]}")

print()

# Issue 6: All cluster details
print("=== ALL CLUSTERS ===")
for i, cl in enumerate(clusters):
    sdn = cl.get('submitted_display_name', '')
    n_cit = len(cl.get('citations', []))
    ver = cl.get('verified', False)
    cit_texts = [cc.get('citation','')[:50] for cc in cl.get('citations', [])]
    ecns = set(cc.get('extracted_case_name','')[:40] for cc in cl.get('citations', []))
    print(f"  [{i+1}] {sdn}")
    print(f"      {n_cit} cits, verified={ver}, ecns={ecns}")
    for ct in cit_texts:
        print(f"      - {ct}")
    print()

# Issue 7: Narrative/bad cluster display names
print("=== ISSUE: Bad cluster display names ===")
for cl in clusters:
    sdn = cl.get('submitted_display_name', '')
    if len(sdn) > 80 or ('(' in sdn and len(sdn) > 60) or sdn.startswith('IN THE'):
        print(f"  BAD: '{sdn[:100]}'")
    if sdn.endswith(')') and '(' in sdn and 'v.' not in sdn:
        print(f"  PAREN: '{sdn[:100]}'")
