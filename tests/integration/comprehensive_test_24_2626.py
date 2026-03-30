"""
Comprehensive test of 24-2626.pdf with detailed citation analysis
"""

import requests
import PyPDF2
import time
import json

# Extract text from PDF
pdf_path = r"D:\dev\casestrainer\24-2626.pdf"
print("="*80)
print("COMPREHENSIVE TEST: 24-2626.pdf")
print("="*80)
print("\nExtracting text from PDF...")
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

print(f"✓ Extracted {len(text):,} characters from {len(reader.pages)} pages\n")

# Send to API
print("Sending to CaseStrainer API...")
start_time = time.time()

response = requests.post(
    'http://localhost:5000/casestrainer/api/analyze',
    json={'text': text},
    timeout=120
)

if response.status_code != 200:
    print(f"ERROR: API returned status {response.status_code}")
    print(response.text)
    exit(1)

result = response.json()
task_id = result.get('task_id') or result.get('request_id')

if task_id and result.get('status') != 'completed':
    print(f"Task queued: {task_id}")
    print("Waiting for async processing...")
    
    # Poll for completion
    max_wait = 60
    poll_interval = 1
    for attempt in range(max_wait):
        time.sleep(poll_interval)
        
        status_response = requests.get(
            f'http://localhost:5000/casestrainer/api/task_status/{task_id}',
            timeout=10
        )
        
        if status_response.status_code != 200:
            continue
            
        status_data = status_response.json()
        
        if status_data.get('status') == 'completed':
            result = status_data
            elapsed = time.time() - start_time
            print(f"✓ Processing completed in {elapsed:.1f}s\n")
            break
        elif status_data.get('status') == 'failed':
            print(f"ERROR: Processing failed: {status_data.get('error')}")
            exit(1)
        
        if attempt % 2 == 0:  # Every 2 seconds
            progress = status_data.get('progress_data', {})
            current_step = progress.get('current_message', 'Processing...')
            print(f"  [{attempt+1}s] {current_step}", end='\r')
    else:
        print(f"\nTimeout waiting for completion after {max_wait}s")
        exit(1)

citations = result.get('citations', [])
clusters = result.get('clusters', [])

print("="*80)
print("EXTRACTION RESULTS SUMMARY")
print("="*80)
print(f"\nTotal Citations Extracted: {len(citations)}")
print(f"Total Clusters Created: {len(clusters)}")
print(f"Processing Time: {elapsed:.1f} seconds")
print(f"Throughput: {len(citations)/elapsed:.1f} citations/second")

# Detailed analysis
print("\n" + "="*80)
print("DETAILED CITATION ANALYSIS (All 65 Citations)")
print("="*80)

# Categorize citations
by_reporter = {}
by_court = {}
case_name_quality = {
    'excellent': [],  # Complete case name
    'good': [],       # Partial but useful
    'missing': [],    # N/A or empty
    'problematic': [] # Fragments, signal words, etc
}

problem_phrases = ['we do not', 'this holding', 'recused', 'superseded by', 'amended by', 'decision in']
signal_patterns = ['see ', 'cf.', 'compare ', 'citing ', 'quoting ', 'discussing ']

for idx, cit in enumerate(citations, 1):
    citation_text = cit.get('citation', '')
    case_name = cit.get('extracted_case_name', 'N/A')
    date = cit.get('extracted_date', 'N/A')
    verified = cit.get('verified', False)
    canonical_name = cit.get('canonical_name')
    
    # Extract reporter type
    if 'U.S.' in citation_text:
        reporter = 'U.S. Supreme Court'
    elif 'F.2d' in citation_text or 'F.3d' in citation_text or 'F.4th' in citation_text:
        reporter = 'Federal Reporter'
    elif 'F. Supp' in citation_text:
        reporter = 'Federal Supplement'
    elif 'P.2d' in citation_text or 'P.3d' in citation_text:
        reporter = 'Pacific Reporter'
    else:
        reporter = 'Other'
    
    by_reporter[reporter] = by_reporter.get(reporter, 0) + 1
    
    # Quality assessment
    if case_name == 'N/A' or not case_name:
        quality = 'missing'
        case_name_quality['missing'].append((idx, citation_text, case_name))
    elif any(phrase in case_name.lower() for phrase in problem_phrases):
        quality = 'problematic'
        case_name_quality['problematic'].append((idx, citation_text, case_name))
    elif any(signal in case_name.lower() for signal in signal_patterns):
        quality = 'problematic'
        case_name_quality['problematic'].append((idx, citation_text, case_name))
    elif ' v. ' in case_name or ' v ' in case_name.lower():
        quality = 'excellent'
        case_name_quality['excellent'].append((idx, citation_text, case_name, date))
    else:
        quality = 'good'
        case_name_quality['good'].append((idx, citation_text, case_name, date))

# Print breakdown by reporter
print("\n" + "-"*80)
print("CITATIONS BY REPORTER TYPE")
print("-"*80)
for reporter, count in sorted(by_reporter.items(), key=lambda x: x[1], reverse=True):
    pct = count/len(citations)*100
    print(f"  {reporter:30s}: {count:3d} citations ({pct:5.1f}%)")

# Print quality breakdown
print("\n" + "-"*80)
print("CASE NAME QUALITY BREAKDOWN")
print("-"*80)

excellent_count = len(case_name_quality['excellent'])
good_count = len(case_name_quality['good'])
missing_count = len(case_name_quality['missing'])
problematic_count = len(case_name_quality['problematic'])

print(f"\n  Excellent (full case name with v.): {excellent_count:3d} ({excellent_count/len(citations)*100:5.1f}%)")
print(f"  Good (partial but useful):          {good_count:3d} ({good_count/len(citations)*100:5.1f}%)")
print(f"  Missing (N/A or empty):             {missing_count:3d} ({missing_count/len(citations)*100:5.1f}%)")
print(f"  Problematic (fragments/signals):    {problematic_count:3d} ({problematic_count/len(citations)*100:5.1f}%)")

# Show examples of excellent extractions
print("\n" + "-"*80)
print("EXCELLENT EXTRACTIONS (First 10)")
print("-"*80)
for idx, cit, name, date in case_name_quality['excellent'][:10]:
    print(f"\n  [{idx}] {cit}")
    print(f"      Case: {name}")
    print(f"      Date: {date}")

# Show problematic cases if any
if case_name_quality['missing']:
    print("\n" + "-"*80)
    print("MISSING CASE NAMES (First 10)")
    print("-"*80)
    for idx, cit, name in case_name_quality['missing'][:10]:
        print(f"\n  [{idx}] {cit}")
        print(f"      Case: {name}")

# Date extraction stats
print("\n" + "-"*80)
print("DATE EXTRACTION ANALYSIS")
print("-"*80)
with_dates = sum(1 for c in citations if c.get('extracted_date'))
date_pct = with_dates/len(citations)*100
print(f"\n  Citations with dates: {with_dates}/{len(citations)} ({date_pct:.1f}%)")

# Verification stats
print("\n" + "-"*80)
print("VERIFICATION STATUS")
print("-"*80)
verified_count = sum(1 for c in citations if c.get('verified') or c.get('canonical_name'))
verified_pct = verified_count/len(citations)*100 if citations else 0
print(f"\n  Verified citations: {verified_count}/{len(citations)} ({verified_pct:.1f}%)")

# Clustering stats
print("\n" + "-"*80)
print("CLUSTERING ANALYSIS")
print("-"*80)
print(f"\n  Total clusters: {len(clusters)}")
if clusters:
    cluster_sizes = [len(c.get('members', [])) for c in clusters if isinstance(c, dict)]
    if cluster_sizes:
        avg_cluster_size = sum(cluster_sizes) / len(cluster_sizes)
        print(f"  Average cluster size: {avg_cluster_size:.1f} citations")
        print(f"  Largest cluster: {max(cluster_sizes)} citations")
        print(f"  Singleton clusters: {sum(1 for s in cluster_sizes if s == 1)}")

# Overall quality score
print("\n" + "="*80)
print("OVERALL QUALITY SCORE")
print("="*80)
quality_score = (excellent_count + good_count) / len(citations) * 100
print(f"\nUsable Case Names: {excellent_count + good_count}/{len(citations)} ({quality_score:.1f}%)")
print(f"Date Extraction: {with_dates}/{len(citations)} ({date_pct:.1f}%)")
print(f"Verification Rate: {verified_count}/{len(citations)} ({verified_pct:.1f}%)")

# Final grade
print("\n" + "-"*80)
if quality_score >= 90 and date_pct >= 95:
    grade = "A - EXCELLENT"
elif quality_score >= 80 and date_pct >= 90:
    grade = "B - GOOD"
elif quality_score >= 70 and date_pct >= 85:
    grade = "C - ACCEPTABLE"
else:
    grade = "D - NEEDS IMPROVEMENT"

print(f"Overall Grade: {grade}")
print("-"*80)

print("\n✓ Comprehensive test completed!")
