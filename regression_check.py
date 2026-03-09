"""Regression check: compare current results against known baselines."""
import json, sys

def analyze(filepath, label, expected_cit_range, expected_cl_range, key_cases=None):
    """Analyze a result file against expected baselines."""
    try:
        data = json.load(open(filepath, 'r', encoding='utf-8'))
    except Exception as e:
        print(f"[FAIL] {label}: Cannot load {filepath}: {e}")
        return False
    
    status = data.get('status', '?')
    cits = data.get('citations', [])
    clusters = data.get('clusters', [])
    n_cit = len(cits)
    n_cl = len(clusters)
    
    ok = True
    issues = []
    
    # Check status
    if status != 'completed':
        issues.append(f"status={status} (expected completed)")
        ok = False
    
    # Check citation count in expected range
    if not (expected_cit_range[0] <= n_cit <= expected_cit_range[1]):
        issues.append(f"citations={n_cit} (expected {expected_cit_range[0]}-{expected_cit_range[1]})")
        ok = False
    
    # Check cluster count in expected range
    if not (expected_cl_range[0] <= n_cl <= expected_cl_range[1]):
        issues.append(f"clusters={n_cl} (expected {expected_cl_range[0]}-{expected_cl_range[1]})")
        ok = False
    
    # Check for N/A case names (should be minority)
    na_count = sum(1 for c in cits if (c.get('extracted_case_name') or '').strip() in ('', 'N/A'))
    na_pct = (na_count / n_cit * 100) if n_cit else 0
    if na_pct > 60:
        issues.append(f"N/A rate={na_pct:.0f}% ({na_count}/{n_cit}) - too high")
        ok = False
    
    # Check verified count
    ver_count = sum(1 for c in cits if c.get('verified'))
    ver_pct = (ver_count / n_cit * 100) if n_cit else 0
    
    # Check key cases if provided
    key_results = []
    if key_cases:
        cluster_names = [cl.get('submitted_display_name', '') for cl in clusters]
        for case_name, should_exist in key_cases:
            found = any(case_name.lower() in cn.lower() for cn in cluster_names)
            status_str = "FOUND" if found else "MISSING"
            if found != should_exist:
                issues.append(f"Key case '{case_name}': {status_str} (expected {'present' if should_exist else 'absent'})")
                ok = False
            key_results.append((case_name, found, should_exist))
    
    # Check for narrative names in clusters
    narrative_clusters = []
    for cl in clusters:
        sdn = cl.get('submitted_display_name', '')
        if len(sdn) > 60 and ' v. ' not in sdn and 'In re' not in sdn:
            narrative_clusters.append(sdn[:50])
    if narrative_clusters:
        issues.append(f"Narrative cluster names: {narrative_clusters[:3]}")
    
    # Print results
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {label}: {n_cit} citations, {n_cl} clusters, {ver_count} verified ({ver_pct:.0f}%), {na_count} N/A ({na_pct:.0f}%)")
    if issues:
        for iss in issues:
            print(f"  - {iss}")
    if key_results:
        for case_name, found, should_exist in key_results:
            tag2 = "OK" if found == should_exist else "ISSUE"
            print(f"  [{tag2}] '{case_name}': {'found' if found else 'missing'}")
    print()
    return ok


all_pass = True

# 1028814.pdf - Known baseline: 213 citations, 61 clusters (was 68 before fixes)
print("=" * 70)
print("REGRESSION TEST RESULTS")
print("=" * 70)
print()

r = analyze(
    'logs/reg_1028814_v5.json', '1028814.pdf (WA appellate brief)',
    expected_cit_range=(200, 225),
    expected_cl_range=(55, 70),
    key_cases=[
        ('Benjamin', True),
        ('Key Design', True),
        ('Greengo', True),
        ('State v. Barber', True),
    ]
)
all_pass = all_pass and r

# 1033397.pdf
r = analyze(
    'logs/reg_1033397_v5.json', '1033397.pdf',
    expected_cit_range=(140, 180),
    expected_cl_range=(35, 55),
)
all_pass = all_pass and r

# 1031351.pdf
r = analyze(
    'logs/reg_1031351_v5.json', '1031351.pdf',
    expected_cit_range=(180, 220),
    expected_cl_range=(60, 85),
)
all_pass = all_pass and r

# 20-297_4g25.pdf (SCOTUS opinion)
r = analyze(
    'logs/reg_20297_v5.json', '20-297_4g25.pdf (SCOTUS opinion)',
    expected_cit_range=(130, 170),
    expected_cl_range=(55, 80),
)
all_pass = all_pass and r

# trumpvbarbaracertpet.pdf - v13 results
r = analyze(
    'logs/reg_trump_v5.json', 'trumpvbarbaracertpet.pdf (SCOTUS cert petition)',
    expected_cit_range=(210, 250),
    expected_cl_range=(85, 105),
    key_cases=[
        ('Pizarro', True),
        ('Venus', True),
        ('Slaughter-House', True),
        ('Murray', True),
        ('Wong Kim Ark', True),
        ('Schooner Exchange', True),
    ]
)
all_pass = all_pass and r

print("=" * 70)
print(f"OVERALL: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
print("=" * 70)
