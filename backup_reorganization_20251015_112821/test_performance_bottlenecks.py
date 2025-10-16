"""Test to identify performance bottlenecks in processing phases"""
import subprocess
import sys
import re
import time

print("=" * 80)
print("PERFORMANCE BOTTLENECK ANALYSIS")
print("=" * 80)
print()

# Run test and capture timing
print("[TEST] Running PDF upload test with timing analysis...")
start = time.time()

result = subprocess.run(
    [sys.executable, "test_upload.py"],
    capture_output=True,
    text=True
)

total_time = time.time() - start
print(f"[TOTAL] Processing completed in {total_time:.2f}s\n")

# Now check Docker logs for phase timings
print("[ANALYSIS] Checking Docker logs for phase timings...")
print("-" * 80)

log_result = subprocess.run(
    ["docker", "logs", "casestrainer-backend-prod", "--tail", "500"],
    capture_output=True,
    text=True
)

logs = log_result.stdout + log_result.stderr

# Extract phase timings
phase_patterns = {
    'PDF Extraction': r'PDF text extraction.*?(\d+\.?\d*)\s*s',
    'Citation Detection': r'(?:Phase 1|Step 1).*?(?:detect|extract).*?citation',
    'Metadata Extraction': r'(?:Phase 2|Step 2).*?metadata',
    'Parallel Detection': r'(?:Phase 2|After parallel detection|parallel citations)',
    'Clustering': r'(?:Phase 5|MASTER_CLUSTER|Creating.*cluster)',
    'Verification': r'(?:verif|VERIFY)',
    'Total Pipeline': r'UNIFIED_PIPELINE.*?complet.*?(\d+\.?\d*)\s*s',
}

# Look for timing logs
timing_entries = []
for line in logs.split('\n'):
    # Look for MASTER_CLUSTER timing
    if 'MASTER_CLUSTER' in line and 'Completed clustering in' in line:
        match = re.search(r'(\d+\.?\d*)s', line)
        if match:
            timing_entries.append(('Clustering (MASTER)', float(match.group(1))))
    
    # Look for phase completion times
    if 'Phase' in line or 'Step' in line:
        match = re.search(r'(\d+\.?\d*)\s*(?:seconds|sec|s\b)', line)
        if match:
            phase_name = line.split(':')[0].split('-')[-1].strip()
            timing_entries.append((phase_name, float(match.group(1))))

# Show phase counts
print("\n[PHASE COUNTS]")
phase_counts = {}
for line in logs.split('\n'):
    if 'UNIFIED_PIPELINE' in line:
        for phase_match in re.finditer(r'Phase \d+[^:]*:', line):
            phase = phase_match.group(0).strip(':')
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

for phase, count in sorted(phase_counts.items()):
    print(f"  {phase}: {count} occurrences")

# Show specific metrics
print("\n[KEY METRICS]")

# Citation counts
citations_match = re.search(r'(\d+)\s+citations', logs, re.IGNORECASE)
if citations_match:
    print(f"  Total Citations: {citations_match.group(1)}")

clusters_match = re.search(r'Created\s+(\d+)\s+(?:final\s+)?clusters', logs, re.IGNORECASE)
if clusters_match:
    print(f"  Total Clusters: {clusters_match.group(1)}")

# Re-extraction count
reextract_count = len(re.findall(r'CLUSTERING-REEXTRACTED', logs))
print(f"  Re-extractions: {reextract_count}")

# Verification count
verify_count = len(re.findall(r'verification', logs, re.IGNORECASE))
print(f"  Verification calls: {verify_count}")

# Show any timing entries found
if timing_entries:
    print("\n[TIMING ENTRIES FOUND]")
    for name, duration in timing_entries:
        print(f"  {name}: {duration:.2f}s")

# Look for slow operations
print("\n[POTENTIAL BOTTLENECKS]")

# Check for re-extraction overhead
if reextract_count > 0:
    avg_time_per_reextract = total_time / max(reextract_count, 1)
    print(f"  ⚠️  Re-extraction: {reextract_count} calls (avg ~{avg_time_per_reextract:.3f}s per call)")

# Check for verification overhead
verified_match = re.search(r'Verified Citations:\s+(\d+)', result.stdout)
if verified_match:
    verified = int(verified_match.group(1))
    if verified > 0:
        print(f"  ⚠️  Verification: {verified} citations verified")

# Check clustering time
for name, duration in timing_entries:
    if 'Cluster' in name or 'MASTER' in name:
        percentage = (duration / total_time) * 100 if total_time > 0 else 0
        print(f"  📊 Clustering: {duration:.2f}s ({percentage:.1f}% of total)")

# General recommendations
print("\n[RECOMMENDATIONS]")
print("  Based on the analysis:")

if reextract_count > 20:
    print("  - High re-extraction count suggests eyecite truncation is common")
    print("    → Consider preventing eyecite extraction entirely")
elif reextract_count > 0:
    print(f"  - {reextract_count} re-extractions performed (truncation fix working)")

if total_time > 10:
    print(f"  - Total processing time is {total_time:.1f}s for 51 citations")
    print(f"    → Average: {total_time/51:.2f}s per citation")
else:
    print(f"  ✅ Processing time is reasonable: {total_time:.1f}s")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
