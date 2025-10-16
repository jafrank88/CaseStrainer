"""
Comprehensive evaluation of production results
Checks: clustering, name extraction, year extraction, verification
"""
import requests
import json
import time
from collections import defaultdict

# Test the production endpoint
url = "https://wolf.law.uw.edu/casestrainer/api/analyze"

payload = {
    "type": "url",
    "url": "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
}

print("="*80)
print("COMPREHENSIVE PRODUCTION EVALUATION")
print("="*80)
print(f"\nEndpoint: {url}")
print(f"Document: {payload['url']}")
print("\n" + "="*80)

try:
    # Submit the analysis request
    print("\n1. SUBMITTING REQUEST...")
    response = requests.post(url, json=payload, verify=False, timeout=30)
    result = response.json()
    
    task_id = result.get('task_id') or result.get('request_id')
    print(f"   Task ID: {task_id}")
    
    # Poll for results
    print("\n2. WAITING FOR PROCESSING...")
    status_url = f"https://wolf.law.uw.edu/casestrainer/api/task_status/{task_id}"
    
    for attempt in range(60):
        time.sleep(5)
        status_response = requests.get(status_url, verify=False, timeout=10)
        status_data = status_response.json()
        
        status = status_data.get('status', 'unknown')
        if status in ['completed', 'failed', 'error']:
            break
    
    # Extract results
    result_data = status_data.get('result', {})
    citations = result_data.get('citations', [])
    clusters = result_data.get('clusters', [])
    
    print(f"\n{'='*80}")
    print("3. OVERALL STATISTICS")
    print(f"{'='*80}")
    print(f"Total Citations: {len(citations)}")
    print(f"Total Clusters: {len(clusters)}")
    print(f"Processing Time: {result_data.get('processing_time_ms', 0) / 1000:.2f}s")
    
    # EVALUATION 1: NAME EXTRACTION
    print(f"\n{'='*80}")
    print("4. NAME EXTRACTION EVALUATION")
    print(f"{'='*80}")
    
    names_extracted = 0
    names_na = 0
    names_truncated = 0
    names_good = 0
    
    for cit in citations:
        extracted_name = cit.get('extracted_case_name', 'N/A')
        if extracted_name and extracted_name != 'N/A':
            names_extracted += 1
            # Check for truncation (very short names or ending with incomplete words)
            if len(extracted_name) < 10 or extracted_name.endswith(('Inc.', 'v.', 'Co.')):
                names_truncated += 1
                if names_truncated <= 5:  # Show first 5
                    print(f"   ⚠️  Truncated: {cit.get('citation')} → '{extracted_name}'")
            else:
                names_good += 1
        else:
            names_na += 1
    
    print(f"\nName Extraction Summary:")
    print(f"   ✅ Good names: {names_good} ({names_good/len(citations)*100:.1f}%)")
    print(f"   ⚠️  Truncated: {names_truncated} ({names_truncated/len(citations)*100:.1f}%)")
    print(f"   ❌ N/A: {names_na} ({names_na/len(citations)*100:.1f}%)")
    
    # EVALUATION 2: YEAR EXTRACTION
    print(f"\n{'='*80}")
    print("5. YEAR EXTRACTION EVALUATION")
    print(f"{'='*80}")
    
    years_extracted = 0
    years_na = 0
    years_valid = 0
    
    for cit in citations:
        extracted_date = cit.get('extracted_date', 'N/A')
        if extracted_date and extracted_date != 'N/A':
            years_extracted += 1
            # Check if it's a valid year (4 digits, reasonable range)
            try:
                year = int(extracted_date)
                if 1800 <= year <= 2025:
                    years_valid += 1
                else:
                    print(f"   ⚠️  Invalid year: {cit.get('citation')} → {extracted_date}")
            except:
                print(f"   ⚠️  Non-numeric year: {cit.get('citation')} → {extracted_date}")
        else:
            years_na += 1
    
    print(f"\nYear Extraction Summary:")
    print(f"   ✅ Valid years: {years_valid} ({years_valid/len(citations)*100:.1f}%)")
    print(f"   ❌ N/A: {years_na} ({years_na/len(citations)*100:.1f}%)")
    
    # EVALUATION 3: CLUSTERING
    print(f"\n{'='*80}")
    print("6. CLUSTERING EVALUATION")
    print(f"{'='*80}")
    
    clustered_citations = 0
    unclustered_citations = 0
    cluster_sizes = defaultdict(int)
    
    for cit in citations:
        cluster_id = cit.get('cluster_id')
        is_in_cluster = cit.get('is_in_cluster', False)
        
        if cluster_id or is_in_cluster:
            clustered_citations += 1
            if cluster_id:
                cluster_sizes[cluster_id] += 1
        else:
            unclustered_citations += 1
    
    print(f"\nClustering Summary:")
    print(f"   Total clusters: {len(clusters)}")
    print(f"   Clustered citations: {clustered_citations} ({clustered_citations/len(citations)*100:.1f}%)")
    print(f"   Unclustered citations: {unclustered_citations} ({unclustered_citations/len(citations)*100:.1f}%)")
    
    if len(clusters) > 0:
        print(f"\n   Cluster Details:")
        for i, cluster in enumerate(clusters[:10], 1):  # Show first 10
            cluster_id = cluster.get('cluster_id', 'unknown')
            cluster_name = cluster.get('cluster_case_name', 'N/A')
            members = cluster.get('members', [])
            print(f"   {i}. {cluster_id}: '{cluster_name}' ({len(members)} citations)")
            if len(members) > 0:
                print(f"      Members: {', '.join(members[:5])}")
    else:
        print(f"\n   ⚠️  WARNING: No clusters found!")
        print(f"   Expected: Parallel citations should be clustered")
        print(f"   Example: '183 Wn.2d 649' and '370 P.3d 157' should cluster together")
    
    # EVALUATION 4: VERIFICATION
    print(f"\n{'='*80}")
    print("7. VERIFICATION EVALUATION")
    print(f"{'='*80}")
    
    verified_count = 0
    unverified_count = 0
    verification_sources = defaultdict(int)
    canonical_names = 0
    canonical_dates = 0
    
    for cit in citations:
        verified = cit.get('verified', False)
        verification_status = cit.get('verification_status', 'unknown')
        
        if verified:
            verified_count += 1
            source = cit.get('verification_source', 'unknown')
            verification_sources[source] += 1
            
            # Check canonical data
            if cit.get('canonical_name'):
                canonical_names += 1
            if cit.get('canonical_date'):
                canonical_dates += 1
        else:
            unverified_count += 1
    
    print(f"\nVerification Summary:")
    print(f"   ✅ Verified: {verified_count} ({verified_count/len(citations)*100:.1f}%)")
    print(f"   ❌ Unverified: {unverified_count} ({unverified_count/len(citations)*100:.1f}%)")
    
    if verification_sources:
        print(f"\n   Verification Sources:")
        for source, count in sorted(verification_sources.items(), key=lambda x: x[1], reverse=True):
            print(f"      {source}: {count} citations")
    
    print(f"\n   Canonical Data:")
    print(f"      Names: {canonical_names} ({canonical_names/len(citations)*100:.1f}%)")
    print(f"      Dates: {canonical_dates} ({canonical_dates/len(citations)*100:.1f}%)")
    
    # EVALUATION 5: SAMPLE CITATIONS
    print(f"\n{'='*80}")
    print("8. SAMPLE CITATIONS (First 10)")
    print(f"{'='*80}")
    
    for i, cit in enumerate(citations[:10], 1):
        citation_text = cit.get('citation', 'N/A')
        extracted_name = cit.get('extracted_case_name', 'N/A')
        extracted_date = cit.get('extracted_date', 'N/A')
        canonical_name = cit.get('canonical_name', 'N/A')
        canonical_date = cit.get('canonical_date', 'N/A')
        verified = '✅' if cit.get('verified') else '❌'
        cluster_id = cit.get('cluster_id', 'none')
        
        print(f"\n{i}. {citation_text}")
        print(f"   Extracted: '{extracted_name}' ({extracted_date})")
        print(f"   Canonical: '{canonical_name}' ({canonical_date})")
        print(f"   Verified: {verified} | Cluster: {cluster_id}")
    
    # EVALUATION 6: ISSUES FOUND
    print(f"\n{'='*80}")
    print("9. ISSUES IDENTIFIED")
    print(f"{'='*80}")
    
    issues = []
    
    if names_na > len(citations) * 0.3:
        issues.append(f"⚠️  HIGH: {names_na} citations ({names_na/len(citations)*100:.1f}%) have no extracted case name")
    
    if names_truncated > len(citations) * 0.1:
        issues.append(f"⚠️  MEDIUM: {names_truncated} citations ({names_truncated/len(citations)*100:.1f}%) have truncated names")
    
    if len(clusters) == 0:
        issues.append(f"⚠️  HIGH: No clusters found - parallel citation detection may not be working")
    
    if verified_count < len(citations) * 0.1:
        issues.append(f"⚠️  HIGH: Only {verified_count} citations ({verified_count/len(citations)*100:.1f}%) verified")
    
    if canonical_names < verified_count * 0.8:
        issues.append(f"⚠️  MEDIUM: Only {canonical_names}/{verified_count} verified citations have canonical names")
    
    if issues:
        for issue in issues:
            print(f"   {issue}")
    else:
        print(f"   ✅ No major issues detected!")
    
    # FINAL SCORE
    print(f"\n{'='*80}")
    print("10. OVERALL EVALUATION SCORE")
    print(f"{'='*80}")
    
    score = 0
    max_score = 5
    
    # Name extraction (0-1 points)
    name_score = names_good / len(citations)
    score += name_score
    print(f"   Name Extraction: {name_score:.2f}/1.00 ({names_good}/{len(citations)} good)")
    
    # Year extraction (0-1 points)
    year_score = years_valid / len(citations)
    score += year_score
    print(f"   Year Extraction: {year_score:.2f}/1.00 ({years_valid}/{len(citations)} valid)")
    
    # Clustering (0-1 points)
    cluster_score = min(1.0, len(clusters) / 10)  # Expect at least 10 clusters
    score += cluster_score
    print(f"   Clustering: {cluster_score:.2f}/1.00 ({len(clusters)} clusters)")
    
    # Verification (0-1 points)
    verification_score = verified_count / len(citations)
    score += verification_score
    print(f"   Verification: {verification_score:.2f}/1.00 ({verified_count}/{len(citations)} verified)")
    
    # Canonical data (0-1 points)
    canonical_score = canonical_names / len(citations) if len(citations) > 0 else 0
    score += canonical_score
    print(f"   Canonical Data: {canonical_score:.2f}/1.00 ({canonical_names}/{len(citations)} with names)")
    
    print(f"\n   {'='*60}")
    print(f"   TOTAL SCORE: {score:.2f}/{max_score} ({score/max_score*100:.1f}%)")
    print(f"   {'='*60}")
    
    if score >= 4.0:
        print(f"   ✅ EXCELLENT - System performing well")
    elif score >= 3.0:
        print(f"   ⚠️  GOOD - Some issues need attention")
    elif score >= 2.0:
        print(f"   ⚠️  FAIR - Multiple issues need fixing")
    else:
        print(f"   ❌ POOR - Major issues need immediate attention")
    
    print(f"\n{'='*80}")
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
