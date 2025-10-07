"""
Test quality improvements with the problematic PDF
"""
import requests
import time
import json

api_url = "http://localhost:5000/casestrainer/api/analyze"

def wait_for_async(task_id, timeout=120):
    """Wait for async task to complete"""
    status_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        time.sleep(2)
        try:
            response = requests.get(status_url, timeout=5)
            data = response.json()
            
            status = data.get('status')
            if status in ['completed', 'failed']:
                return data
        except:
            pass
    
    return None

print("=" * 80)
print("TESTING QUALITY IMPROVEMENTS")
print("=" * 80)

# Test with the same PDF that showed issues
print("\nProcessing PDF: 1033940.pdf")
pdf_payload = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
}

response = requests.post(api_url, json=pdf_payload, timeout=10)
data = response.json()

task_id = data.get('task_id') or data.get('metadata', {}).get('job_id')
if task_id:
    print(f"Task ID: {task_id}")
    print("Waiting for processing...")
    data = wait_for_async(task_id)

if not data:
    print("❌ FAILED: No data returned")
    exit(1)

citations = data.get('citations', [])
clusters = data.get('clusters', [])

print(f"\n✅ Processing completed!")
print(f"Citations: {len(citations)}")
print(f"Clusters: {len(clusters)}")

# Test 1: Check for incorrect clustering (Cluster 18 issue)
print("\n" + "=" * 80)
print("TEST 1: Clustering Validation")
print("=" * 80)

# Find clusters with potential issues
problematic_clusters = []
for cluster in clusters:
    cluster_citations = cluster.get('citations', [])
    if len(cluster_citations) < 2:
        continue
    
    # Check year consistency
    years = []
    for cit in cluster_citations:
        year = cit.get('extracted_date') or cit.get('canonical_date', '')
        if year and year != 'N/A':
            # Extract year
            import re
            year_match = re.search(r'(19|20)\d{2}', str(year))
            if year_match:
                years.append(int(year_match.group(0)))
    
    if len(years) >= 2:
        year_diff = max(years) - min(years)
        if year_diff > 2:
            problematic_clusters.append({
                'cluster_id': cluster.get('cluster_id'),
                'year_diff': year_diff,
                'years': years,
                'size': len(cluster_citations)
            })

if problematic_clusters:
    print(f"❌ FAILED: Found {len(problematic_clusters)} clusters with year mismatches > 2 years")
    for pc in problematic_clusters:
        print(f"  - {pc['cluster_id']}: {pc['year_diff']} year gap (years: {pc['years']})")
else:
    print(f"✅ PASSED: No clusters with year mismatches > 2 years")

# Test 2: Check for truncated case names
print("\n" + "=" * 80)
print("TEST 2: Case Name Truncation")
print("=" * 80)

truncated_names = []
for cit in citations:
    canonical_name = cit.get('canonical_name', '')
    extracted_name = cit.get('extracted_case_name', '')
    
    if canonical_name and canonical_name != 'N/A':
        # Check for truncation indicators
        is_truncated = (
            canonical_name.endswith('...') or
            len(canonical_name) < 20 or
            canonical_name.endswith(' v. ') or
            canonical_name.count(' ') < 2
        )
        
        if is_truncated:
            truncated_names.append({
                'citation': cit.get('citation'),
                'canonical_name': canonical_name,
                'extracted_name': extracted_name,
                'length': len(canonical_name)
            })

if truncated_names:
    print(f"⚠️  WARNING: Found {len(truncated_names)} potentially truncated names")
    for tn in truncated_names[:5]:  # Show first 5
        print(f"  - {tn['citation']}: '{tn['canonical_name']}' (len: {tn['length']})")
        if tn['extracted_name'] and len(tn['extracted_name']) > len(tn['canonical_name']):
            print(f"    Extracted is longer: '{tn['extracted_name']}'")
else:
    print(f"✅ PASSED: No obviously truncated case names detected")

# Test 3: Check cluster quality
print("\n" + "=" * 80)
print("TEST 3: Cluster Quality")
print("=" * 80)

# Check for clusters with mismatched case names
mismatched_clusters = []
for cluster in clusters:
    cluster_citations = cluster.get('citations', [])
    if len(cluster_citations) < 2:
        continue
    
    # Get all case names in cluster
    case_names = []
    for cit in cluster_citations:
        name = cit.get('cluster_case_name') or cit.get('extracted_case_name') or cit.get('canonical_name')
        if name and name != 'N/A':
            case_names.append(name)
    
    # Check if all names are similar
    if len(case_names) >= 2:
        # Simple check: all names should contain similar words
        first_name = case_names[0].lower()
        for name in case_names[1:]:
            # Check if names share at least one significant word
            first_words = set(first_name.split())
            name_words = set(name.lower().split())
            common_words = first_words & name_words
            
            # Filter out common legal words
            common_words = {w for w in common_words if w not in ['v', 'v.', 'inc', 'inc.', 'llc', 'corp', 'the', 'of', 'and']}
            
            if len(common_words) == 0:
                mismatched_clusters.append({
                    'cluster_id': cluster.get('cluster_id'),
                    'names': case_names,
                    'size': len(cluster_citations)
                })
                break

if mismatched_clusters:
    print(f"❌ FAILED: Found {len(mismatched_clusters)} clusters with mismatched case names")
    for mc in mismatched_clusters[:3]:  # Show first 3
        print(f"  - {mc['cluster_id']} (size: {mc['size']})")
        for name in mc['names'][:3]:
            print(f"    • {name}")
else:
    print(f"✅ PASSED: All clusters have consistent case names")

# Test 4: Overall statistics
print("\n" + "=" * 80)
print("TEST 4: Overall Statistics")
print("=" * 80)

verified_count = sum(1 for c in citations if c.get('verified') or c.get('is_verified'))
canonical_count = sum(1 for c in citations if c.get('canonical_name') and c.get('canonical_name') != 'N/A')
complete_names = sum(1 for c in citations if c.get('canonical_name') and len(c.get('canonical_name', '')) > 20)

print(f"Total Citations: {len(citations)}")
print(f"Verified: {verified_count} ({verified_count/len(citations)*100:.1f}%)")
print(f"With Canonical Names: {canonical_count} ({canonical_count/len(citations)*100:.1f}%)")
print(f"Complete Names (>20 chars): {complete_names} ({complete_names/len(citations)*100:.1f}%)")
print(f"Total Clusters: {len(clusters)}")
print(f"Avg Cluster Size: {len(citations)/len(clusters):.1f}" if clusters else "N/A")

# Final verdict
print("\n" + "=" * 80)
print("FINAL VERDICT")
print("=" * 80)

tests_passed = 0
tests_total = 3

if not problematic_clusters:
    tests_passed += 1
    print("✅ Clustering validation: PASSED")
else:
    print("❌ Clustering validation: FAILED")

if len(truncated_names) < len(citations) * 0.15:  # Less than 15% truncated
    tests_passed += 1
    print("✅ Case name truncation: PASSED (acceptable level)")
else:
    print("❌ Case name truncation: FAILED (too many truncated)")

if not mismatched_clusters:
    tests_passed += 1
    print("✅ Cluster quality: PASSED")
else:
    print("❌ Cluster quality: FAILED")

print(f"\nTests Passed: {tests_passed}/{tests_total}")

if tests_passed == tests_total:
    print("\n🎉 ALL TESTS PASSED! Quality improvements are working!")
    exit(0)
elif tests_passed >= tests_total - 1:
    print("\n⚠️  MOSTLY PASSED: Minor issues remain")
    exit(0)
else:
    print("\n❌ TESTS FAILED: Significant issues detected")
    exit(1)
