"""
Comprehensive analysis of 24-2626.pdf covering all priority areas
Tests P3 (contamination), P4 (multi-plaintiff), P5 (clustering quality)
"""

import requests
import json
from collections import defaultdict, Counter

# Upload fresh
pdf_path = "D:/dev/casestrainer/24-2626.pdf"
url = "http://localhost:5000/casestrainer/api/analyze"

print("=" * 100)
print("COMPREHENSIVE 24-2626 ANALYSIS")
print("=" * 100)
print("\nUploading for fresh analysis...")

with open(pdf_path, 'rb') as f:
    files = {'file': ('24-2626.pdf', f, 'application/pdf')}
    response = requests.post(url, files=files, timeout=300)

if response.status_code != 200:
    print(f"ERROR: {response.status_code}")
    exit(1)

result = response.json()
task_id = result.get('request_id') or result.get('metadata', {}).get('job_id')

if result.get('metadata', {}).get('processing_mode') == 'queued':
    import time
    print(f"Queued: {task_id}, waiting...")
    poll_url = f"http://localhost:5000/casestrainer/api/task_status/{task_id}"
    
    for i in range(60):
        time.sleep(2)
        poll_response = requests.get(poll_url)
        if poll_response.status_code == 200:
            poll_result = poll_response.json()
            if poll_result.get('status') == 'completed':
                result = poll_result
                print("Complete!")
                break
            elif poll_result.get('status') in ('failed', 'error'):
                print(f"Failed: {poll_result.get('error')}")
                exit(1)
    else:
        print("Timeout")
        exit(1)

citations = result.get('citations', [])
clusters = result.get('clusters', [])

print(f"\n📊 BASIC STATS:")
print(f"   Citations: {len(citations)}")
print(f"   Clusters: {len(clusters)}")

# === P3: CONTAMINATION ANALYSIS ===
print("\n" + "=" * 100)
print("P3: CONTAMINATION ANALYSIS")
print("=" * 100)

contaminated = []
for cite in citations:
    name = (cite.get('extracted_case_name', '') or '').lower()
    if any(word in name for word in ['gopher', 'melone', 'thakore']):
        contaminated.append(cite)

contam_rate = len(contaminated) / len(citations) * 100 if citations else 0

if len(contaminated) == 0:
    print(f"\n✅ ✅ ✅ ZERO CONTAMINATION! ({len(citations)} citations clean)")
    print("   P3: PASSED - Contamination filter working!")
elif contam_rate < 5:
    print(f"\n⚠️  Low contamination: {len(contaminated)}/{len(citations)} ({contam_rate:.1f}%)")
    print("   P3: PARTIAL - Some leakage but improved")
else:
    print(f"\n❌ High contamination: {len(contaminated)}/{len(citations)} ({contam_rate:.1f}%)")
    print("   P3: FAILED - Filter not working")
    
if contaminated:
    print(f"\n   Contaminated citations:")
    for cite in contaminated[:5]:
        print(f"      {cite['citation']:30} -> {cite.get('extracted_case_name', '')[:60]}")

# === P4: MULTI-PLAINTIFF DETECTION ===
print("\n" + "=" * 100)
print("P4: MULTI-PLAINTIFF DETECTION")
print("=" * 100)

# Check if "GOPHER MEDIA LLC" appears in contaminated names
# If it does, document detection worked; if not, detection failed
gopher_detected = any('gopher media' in c.get('extracted_case_name', '').lower() for c in contaminated)

print(f"\n   Document should detect: 'GOPHER MEDIA LLC v. MELONE'")
print(f"   (Primary plaintiff, not 'AJAY THAKORE')")

if gopher_detected:
    print(f"\n✅ 'GOPHER MEDIA LLC' found in extractions")
    print("   P4: DETECTION WORKING (but contamination still occurring)")
else:
    print(f"\n❌ 'GOPHER MEDIA LLC' NOT found - only 'THAKORE' detected")
    print("   P4: FAILED - Multi-plaintiff detection not working")

# === P5: CLUSTERING QUALITY ===
print("\n" + "=" * 100)
print("P5: CLUSTERING QUALITY ANALYSIS")
print("=" * 100)

# Cluster size distribution
cluster_sizes = [len(cluster.get('citations', [])) for cluster in clusters]
size_counts = Counter(cluster_sizes)

print(f"\n📊 Cluster Size Distribution:")
for size in sorted(size_counts.keys()):
    count = size_counts[size]
    print(f"   {size} citation(s): {count} clusters")

# False clustering check (same reporter, different volumes)
false_clusters = []
for cluster in clusters:
    cluster_citations = cluster.get('citations', [])
    if len(cluster_citations) < 2:
        continue
    
    # Group by reporter
    reporters = defaultdict(list)
    for cite in cluster_citations:
        citation_text = cite.get('text', '') or cite.get('citation', '')
        
        # Extract reporter
        reporter = None
        for rep in ['F.4th', 'F.3d', 'F.2d', 'U.S.', 'S. Ct.', 'P.3d', 'Cal. Rptr.']:
            if rep in citation_text:
                reporter = rep
                break
        
        if reporter:
            parts = citation_text.strip().split()
            volume = parts[0] if parts else '?'
            reporters[reporter].append({'text': citation_text, 'volume': volume})
    
    # Check for same reporter, different volumes
    for reporter, cites in reporters.items():
        if len(cites) > 1:
            volumes = [c['volume'] for c in cites]
            if len(set(volumes)) > 1:  # Different volumes
                false_clusters.append({
                    'case_name': cluster.get('case_name', 'N/A')[:60],
                    'reporter': reporter,
                    'volumes': sorted(set(volumes))
                })

if false_clusters:
    print(f"\n❌ FALSE CLUSTERING: {len(false_clusters)} clusters")
    print("   P5: FAILED - Same reporter with different volumes clustered together")
    for fc in false_clusters[:5]:
        print(f"      {fc['reporter']}: volumes {fc['volumes']} - '{fc['case_name']}'")
else:
    print(f"\n✅ NO FALSE CLUSTERING detected")
    print("   P5: PASSED - Clustering respects reporter/volume rules")

# Parallel citation detection rate
multi_citation_clusters = sum(1 for cluster in clusters if len(cluster.get('citations', [])) >= 2)
parallel_rate = multi_citation_clusters / len(clusters) * 100 if clusters else 0

print(f"\n📊 Parallel Citation Detection:")
print(f"   Multi-citation clusters: {multi_citation_clusters}/{len(clusters)} ({parallel_rate:.1f}%)")
print(f"   Single-citation clusters: {len(clusters) - multi_citation_clusters}")

if parallel_rate < 10:
    print("   ⚠️  Very few parallel citations detected - may be missing some")
elif parallel_rate > 50:
    print("   ⚠️  High parallel rate - may have false positives")
else:
    print("   ✅ Reasonable parallel citation rate")

# === OVERALL SUMMARY ===
print("\n" + "=" * 100)
print("OVERALL SUMMARY")
print("=" * 100)

scores = []

# P3 score
if contam_rate == 0:
    scores.append(("P3: Contamination", "PASS", "✅"))
elif contam_rate < 5:
    scores.append(("P3: Contamination", "PARTIAL", "⚠️ "))
else:
    scores.append(("P3: Contamination", "FAIL", "❌"))

# P4 score
if gopher_detected:
    scores.append(("P4: Multi-Plaintiff Detection", "WORKING", "✅"))
else:
    scores.append(("P4: Multi-Plaintiff Detection", "FAIL", "❌"))

# P5 score  
if len(false_clusters) == 0:
    scores.append(("P5: Clustering Quality", "PASS", "✅"))
else:
    scores.append(("P5: Clustering Quality", "FAIL", "❌"))

print()
for area, status, emoji in scores:
    print(f"   {emoji} {area:40} {status}")

# Final verdict
passing = sum(1 for _, status, _ in scores if status == "PASS")
total = len(scores)

print(f"\n📊 Final Score: {passing}/{total} priorities passed")

if passing == total:
    print("   🎉 ALL PRIORITIES RESOLVED!")
elif passing >= total / 2:
    print("   ⚠️  Partial success - some issues remain")
else:
    print("   ❌ Major issues remain")

print("\n" + "=" * 100)

# Save detailed results
with open('24-2626_comprehensive_results.json', 'w') as f:
    json.dump({
        'citations': citations,
        'clusters': clusters,
        'contamination_rate': contam_rate,
        'contaminated_citations': [c['citation'] for c in contaminated],
        'false_clusters': false_clusters,
        'cluster_size_distribution': dict(size_counts),
        'scores': scores
    }, f, indent=2)

print("Detailed results saved to 24-2626_comprehensive_results.json")
