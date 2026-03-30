"""
Comprehensive Sync vs Async Comparison for 24-2626.pdf
Tests document with FORCED sync and async processing to compare:
1. Clustering accuracy
2. Case name extraction quality  
3. Year extraction accuracy
4. Contamination filtering effectiveness
"""

import requests
import json
import time
from collections import defaultdict

pdf_path = "D:/dev/casestrainer/24-2626.pdf"
url = "http://localhost:5000/casestrainer/api/analyze"

print("=" * 120)
print("SYNC VS ASYNC COMPARISON: 24-2626.pdf (Gopher Media LLC v. Melone)")
print("=" * 120)
print()

# Function to analyze results
def analyze_results(citations, clusters, mode_name):
    """Analyze citation results for quality metrics"""
    
    print(f"\n{'=' * 120}")
    print(f"{mode_name.upper()} PROCESSING RESULTS")
    print(f"{'=' * 120}")
    
    print(f"\n📊 Basic Metrics:")
    print(f"   Total Citations: {len(citations)}")
    print(f"   Total Clusters: {len(clusters)}")
    
    # === CONTAMINATION CHECK ===
    print(f"\n{'─' * 120}")
    print("1. CONTAMINATION CHECK (Gopher Media / Melone)")
    print(f"{'─' * 120}")
    
    contaminated = []
    document_keywords = ['gopher media', 'gopher', 'melone', 'thakore']
    
    for cite in citations:
        extracted = (cite.get('extracted_case_name', '') or '').lower()
        citation_text = cite.get('citation', '')
        
        # Check for document case name contamination
        for keyword in document_keywords:
            if keyword in extracted and citation_text:
                contaminated.append({
                    'citation': citation_text,
                    'extracted': cite.get('extracted_case_name', ''),
                    'canonical': cite.get('canonical_name', 'N/A'),
                    'keyword': keyword
                })
                break
    
    if contaminated:
        print(f"   ❌ CONTAMINATION DETECTED: {len(contaminated)}/{len(citations)} citations ({len(contaminated)/len(citations)*100:.1f}%)")
        print(f"\n   First 10 contaminated citations:")
        for i, item in enumerate(contaminated[:10], 1):
            print(f"   {i:2d}. {item['citation']:25} → '{item['extracted'][:60]}'")
            print(f"       Keyword: '{item['keyword']}'")
    else:
        print(f"   ✅ NO CONTAMINATION: All citations clean")
    
    # === CASE NAME QUALITY ===
    print(f"\n{'─' * 120}")
    print("2. CASE NAME EXTRACTION QUALITY")
    print(f"{'─' * 120}")
    
    n_a_names = []
    very_short = []
    signal_words = []
    truncated = []
    
    for cite in citations:
        extracted = cite.get('extracted_case_name', '')
        citation_text = cite.get('citation', '')
        
        if extracted in ['N/A', '', None]:
            n_a_names.append(citation_text)
            continue
        
        if len(extracted) < 10:
            very_short.append({'citation': citation_text, 'name': extracted})
        
        signal_words_list = ['see,', 'e.g.', 'also', 'id.', 'citing', 'see e.g.']
        if any(sw in extracted.lower() for sw in signal_words_list):
            signal_words.append({'citation': citation_text, 'name': extracted})
        
        if extracted.endswith(' v.') or extracted.startswith('v. '):
            truncated.append({'citation': citation_text, 'name': extracted})
    
    if len(citations) > 0:
        print(f"   N/A Names: {len(n_a_names)}/{len(citations)} ({len(n_a_names)/len(citations)*100:.1f}%)")
        print(f"   Very Short (<10 chars): {len(very_short)}/{len(citations)} ({len(very_short)/len(citations)*100:.1f}%)")
        print(f"   Signal Words: {len(signal_words)}/{len(citations)} ({len(signal_words)/len(citations)*100:.1f}%)")
        print(f"   Truncated (ends/starts with 'v.'): {len(truncated)}/{len(citations)} ({len(truncated)/len(citations)*100:.1f}%)")
    else:
        print(f"   ⚠️  NO CITATIONS FOUND! Cannot calculate percentages.")
        print(f"   N/A Names: {len(n_a_names)}")
        print(f"   Very Short: {len(very_short)}")
        print(f"   Signal Words: {len(signal_words)}")
        print(f"   Truncated: {len(truncated)}")
    
    if very_short:
        print(f"\n   Very Short Names (first 5):")
        for item in very_short[:5]:
            print(f"      {item['citation']:25} → '{item['name']}'")
    
    if signal_words:
        print(f"\n   Signal Words Present (first 5):")
        for item in signal_words[:5]:
            print(f"      {item['citation']:25} → '{item['name']}'")
    
    # === FALSE CLUSTERING ===
    print(f"\n{'─' * 120}")
    print("3. FALSE CLUSTERING CHECK (Same Reporter, Different Volumes)")
    print(f"{'─' * 120}")
    
    false_clusters = []
    
    for cluster in clusters:
        cluster_citations = cluster.get('citations', [])
        if len(cluster_citations) < 2:
            continue
        
        # Group by reporter
        reporters = defaultdict(list)
        for cite in cluster_citations:
            citation_text = cite.get('text', '') or cite.get('citation', '')
            
            # Extract reporter type
            reporter = None
            for rep in ['F.4th', 'F.3d', 'F.2d', 'F. Supp.', 'U.S.', 'S. Ct.', 'P.3d', 'P.2d', 'Cal. Rptr.']:
                if rep in citation_text:
                    reporter = rep
                    break
            
            if not reporter:
                continue
            
            # Extract volume
            parts = citation_text.strip().split()
            volume = parts[0] if parts else '?'
            
            reporters[reporter].append({
                'text': citation_text,
                'volume': volume
            })
        
        # Check for same reporter, different volumes
        for reporter, cites in reporters.items():
            if len(cites) > 1:
                volumes = [c['volume'] for c in cites]
                unique_volumes = set(volumes)
                
                if len(unique_volumes) > 1:
                    false_clusters.append({
                        'case_name': cluster.get('case_name', 'N/A'),
                        'reporter': reporter,
                        'citations': [c['text'] for c in cites],
                        'volumes': sorted(list(unique_volumes))
                    })
    
    if false_clusters:
        print(f"   ❌ FALSE CLUSTERING DETECTED: {len(false_clusters)} clusters")
        print(f"\n   False Clusters:")
        for i, fc in enumerate(false_clusters[:5], 1):
            print(f"   {i}. Case: {fc['case_name'][:60]}")
            print(f"      Reporter: {fc['reporter']}, Volumes: {fc['volumes']}")
            print(f"      Citations: {fc['citations']}")
    else:
        print(f"   ✅ NO FALSE CLUSTERING: All clusters valid")
    
    # === YEAR EXTRACTION ===
    print(f"\n{'─' * 120}")
    print("4. YEAR EXTRACTION ACCURACY")
    print(f"{'─' * 120}")
    
    missing_years = []
    year_conflicts = []
    
    for cite in citations:
        citation_text = cite.get('citation', '')
        extracted_year = cite.get('extracted_date', '') or cite.get('extracted_year', '')
        canonical_year = cite.get('canonical_date', '') or cite.get('canonical_year', '')
        
        if not extracted_year or extracted_year == 'N/A':
            missing_years.append(citation_text)
        
        if extracted_year and canonical_year and extracted_year != 'N/A' and canonical_year != 'N/A':
            try:
                ext_yr = int(str(extracted_year)[:4])
                can_yr = int(str(canonical_year)[:4])
                
                if abs(ext_yr - can_yr) > 2:
                    year_conflicts.append({
                        'citation': citation_text,
                        'extracted': ext_yr,
                        'canonical': can_yr,
                        'diff': abs(ext_yr - can_yr)
                    })
            except (ValueError, TypeError):
                pass
    
    if len(citations) > 0:
        print(f"   Missing Years: {len(missing_years)}/{len(citations)} ({len(missing_years)/len(citations)*100:.1f}%)")
        print(f"   Year Conflicts (>2 years): {len(year_conflicts)}/{len(citations)}")
    else:
        print(f"   Missing Years: {len(missing_years)}")
        print(f"   Year Conflicts: {len(year_conflicts)}")
    
    if year_conflicts:
        print(f"\n   Year Conflicts (first 5):")
        for item in year_conflicts[:5]:
            print(f"      {item['citation']:25} Extracted: {item['extracted']}, Canonical: {item['canonical']} (Δ{item['diff']} years)")
    
    # === VERIFICATION ===
    print(f"\n{'─' * 120}")
    print("5. VERIFICATION RATE")
    print(f"{'─' * 120}")
    
    verified = sum(1 for c in citations if c.get('verified', False))
    verification_rate = verified / len(citations) * 100 if len(citations) > 0 else 0
    
    if len(citations) > 0:
        print(f"   Verified: {verified}/{len(citations)} ({verification_rate:.1f}%)")
    else:
        print(f"   Verified: {verified} (no citations to verify)")
    
    # Return metrics for comparison
    return {
        'total_citations': len(citations),
        'total_clusters': len(clusters),
        'contaminated': len(contaminated),
        'n_a_names': len(n_a_names),
        'very_short': len(very_short),
        'signal_words': len(signal_words),
        'false_clusters': len(false_clusters),
        'missing_years': len(missing_years),
        'year_conflicts': len(year_conflicts),
        'verified': verified,
        'verification_rate': verification_rate
    }

# === PROCESS SYNC ===
print("\n" + "=" * 120)
print("PROCESSING: SYNC MODE (FORCED)")
print("=" * 120)

with open(pdf_path, 'rb') as f:
    files = {'file': ('24-2626.pdf', f, 'application/pdf')}
    data = {'force_sync': 'true'}  # Force synchronous processing
    
    print("\n[SYNC] Uploading and processing (this may take 60+ seconds)...")
    sync_response = requests.post(url, files=files, data=data, timeout=300)

if sync_response.status_code != 200:
    print(f"[SYNC] ERROR: {sync_response.status_code}")
    print(sync_response.text[:500])
    sync_result = None
    sync_metrics = None
else:
    sync_result = sync_response.json()
    
    # DEBUG: Check what we got back
    print(f"[SYNC] Response keys: {list(sync_result.keys())}")
    
    sync_citations = sync_result.get('citations', [])
    sync_clusters = sync_result.get('clusters', [])
    
    # Check if empty - might be in different location
    if len(sync_citations) == 0:
        print(f"[SYNC] WARNING: No citations in 'citations' key")
        print(f"[SYNC] Full response structure: {json.dumps(sync_result, indent=2)[:1000]}")
    
    print(f"[SYNC] ✓ Completed! Found {len(sync_citations)} citations, {len(sync_clusters)} clusters")
    sync_metrics = analyze_results(sync_citations, sync_clusters, "SYNC")

# === PROCESS ASYNC ===
print("\n\n" + "=" * 120)
print("PROCESSING: ASYNC MODE (FORCED)")
print("=" * 120)

with open(pdf_path, 'rb') as f:
    files = {'file': ('24-2626.pdf', f, 'application/pdf')}
    data = {'force_async': 'true'}  # Force asynchronous processing
    
    print("\n[ASYNC] Uploading...")
    async_response = requests.post(url, files=files, data=data, timeout=300)

if async_response.status_code != 200:
    print(f"[ASYNC] ERROR: {async_response.status_code}")
    print(async_response.text[:500])
    async_result = None
    async_metrics = None
else:
    async_result = async_response.json()
    
    # Check if async
    processing_mode = async_result.get('metadata', {}).get('processing_mode', 'immediate')
    
    if processing_mode == 'queued':
        task_id = async_result.get('request_id') or async_result.get('metadata', {}).get('job_id')
        print(f"[ASYNC] Task queued: {task_id}")
        print("[ASYNC] Polling for completion...")
        
        poll_url = f"http://localhost:5000/casestrainer/api/task/{task_id}"
        
        for i in range(120):  # 4 minutes max
            time.sleep(2)
            poll_response = requests.get(poll_url)
            
            if poll_response.status_code == 200:
                poll_result = poll_response.json()
                status = poll_result.get('status', 'unknown')
                progress = poll_result.get('progress_data', {}).get('overall_progress', 0)
                
                if i % 5 == 0:  # Print every 10 seconds
                    print(f"[ASYNC] Status: {status}, Progress: {progress}%")
                
                if status == 'completed':
                    async_result = poll_result.get('result', {})
                    print(f"[ASYNC] ✓ Completed!")
                    break
                elif status in ('failed', 'error'):
                    print(f"[ASYNC] ✗ Failed: {poll_result.get('error')}")
                    async_result = None
                    break
        else:
            print("[ASYNC] ✗ Timeout")
            async_result = None
    else:
        print("[ASYNC] ✓ Completed immediately (sync fallback)")
    
    if async_result:
        async_citations = async_result.get('citations', [])
        async_clusters = async_result.get('clusters', [])
        async_metrics = analyze_results(async_citations, async_clusters, "ASYNC")
    else:
        async_metrics = None

# === COMPARISON ===
if sync_metrics and async_metrics:
    print("\n\n" + "=" * 120)
    print("SYNC VS ASYNC COMPARISON")
    print("=" * 120)
    
    print(f"\n{'Metric':<30} {'SYNC':<20} {'ASYNC':<20} {'Difference':<20}")
    print("─" * 120)
    
    metrics_to_compare = [
        ('Total Citations', 'total_citations'),
        ('Total Clusters', 'total_clusters'),
        ('Contaminated Citations', 'contaminated'),
        ('N/A Names', 'n_a_names'),
        ('Very Short Names', 'very_short'),
        ('Signal Words', 'signal_words'),
        ('False Clusters', 'false_clusters'),
        ('Missing Years', 'missing_years'),
        ('Year Conflicts', 'year_conflicts'),
        ('Verified Citations', 'verified'),
        ('Verification Rate %', 'verification_rate')
    ]
    
    for label, key in metrics_to_compare:
        sync_val = sync_metrics[key]
        async_val = async_metrics[key]
        
        if key == 'verification_rate':
            diff = f"{async_val - sync_val:+.1f}%"
            sync_str = f"{sync_val:.1f}%"
            async_str = f"{async_val:.1f}%"
        else:
            diff = f"{async_val - sync_val:+d}" if sync_val != async_val else "Same"
            sync_str = str(sync_val)
            async_str = str(async_val)
        
        # Color code the difference
        if sync_val == async_val or diff == "Same":
            status = "✅"
        elif abs(sync_val - async_val) <= 2:
            status = "⚠️ "
        else:
            status = "❌"
        
        print(f"{label:<30} {sync_str:<20} {async_str:<20} {status} {diff}")
    
    print("\n" + "=" * 120)
    print("OVERALL ASSESSMENT")
    print("=" * 120)
    
    # Calculate consistency score
    identical_count = sum(1 for _, key in metrics_to_compare if sync_metrics[key] == async_metrics[key])
    consistency_score = identical_count / len(metrics_to_compare) * 100
    
    print(f"\n📊 Consistency Score: {consistency_score:.1f}% ({identical_count}/{len(metrics_to_compare)} metrics identical)")
    
    # Quality assessment
    issues = []
    
    if sync_metrics['contaminated'] > 0 or async_metrics['contaminated'] > 0:
        issues.append(f"❌ Contamination still present (Sync: {sync_metrics['contaminated']}, Async: {async_metrics['contaminated']})")
    else:
        issues.append("✅ Contamination filter working")
    
    if sync_metrics['false_clusters'] > 0 or async_metrics['false_clusters'] > 0:
        issues.append(f"❌ False clustering detected (Sync: {sync_metrics['false_clusters']}, Async: {async_metrics['false_clusters']})")
    else:
        issues.append("✅ Clustering logic correct")
    
    if sync_metrics['verification_rate'] < 20 or async_metrics['verification_rate'] < 20:
        issues.append(f"⚠️  Low verification rate (Sync: {sync_metrics['verification_rate']:.1f}%, Async: {async_metrics['verification_rate']:.1f}%)")
    else:
        issues.append(f"✅ Good verification rate (Sync: {sync_metrics['verification_rate']:.1f}%, Async: {async_metrics['verification_rate']:.1f}%)")
    
    print("\n📋 Key Findings:")
    for issue in issues:
        print(f"   {issue}")

print("\n" + "=" * 120)
print("TEST COMPLETE")
print("=" * 120)
