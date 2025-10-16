"""
Test 24-2626.pdf with production API - properly waits for async completion.
"""

import requests
import PyPDF2
import time
import json

# Extract text from PDF
pdf_path = r"D:\dev\casestrainer\24-2626.pdf"
print("Extracting text from PDF...")
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

print(f"Extracted {len(text)} characters\n")

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

print(f"DEBUG: task_id={task_id}, success={result.get('success')}, status={result.get('status')}")

if task_id and result.get('status') != 'completed':
    print(f"Task queued: {task_id}")
    print("Waiting for async processing to complete...")
    
    # Poll for completion
    max_wait = 60  # 60 seconds max
    poll_interval = 1  # 1 second
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
            print(f"[OK] Processing completed in {time.time() - start_time:.1f}s")
            break
        elif status_data.get('status') == 'failed':
            print(f"[ERROR] Processing failed: {status_data.get('error')}")
            exit(1)
        
        # Show progress
        progress = status_data.get('progress_data', {})
        current_step = progress.get('current_message', 'Processing...')
        print(f"  [{attempt+1}s] {current_step}", end='\r')
    else:
        print(f"\n⚠️  Timeout waiting for completion after {max_wait}s")
        exit(1)

citations = result.get('citations', [])
clusters = result.get('clusters', [])

print(f"\n\n{'='*80}")
print(f"EXTRACTION RESULTS")
print(f"{'='*80}")
print(f"\nTotal citations: {len(citations)}")
print(f"Total clusters: {len(clusters)}")

if len(citations) == 0:
    print("\n❌ NO CITATIONS FOUND!")
    print("\nFull response:")
    print(json.dumps(result, indent=2))
    exit(1)

# Analyze case name quality
print(f"\n{'='*80}")
print(f"CASE NAME QUALITY ANALYSIS")
print(f"{'='*80}\n")

truncated = []
sentence_fragments = []
signal_words = []
n_a_count = 0
good_count = 0

problem_phrases = ['we do not', 'this holding', 'recused', 'superseded by', 'amended by', 'decision in']
signal_patterns = ['see ', 'cf.', 'compare ', 'citing ', 'quoting ', 'discussing ']

for idx, cit in enumerate(citations[:10], 1):  # Show first 10
    citation_text = cit.get('citation', '')
    case_name = cit.get('extracted_case_name', 'N/A')
    date = cit.get('extracted_date', 'N/A')
    
    print(f"{idx}. {citation_text}")
    print(f"   Case: {case_name}")
    print(f"   Date: {date}")
    
    # Check for issues
    issues = []
    if case_name == 'N/A':
        n_a_count += 1
        issues.append("NO NAME")
    elif any(phrase in case_name.lower() for phrase in problem_phrases):
        sentence_fragments.append(citation_text)
        issues.append("SENTENCE FRAGMENT")
    elif any(signal in case_name.lower() for signal in signal_patterns):
        signal_words.append(citation_text)
        issues.append("SIGNAL WORD")
    elif len(case_name) > 0 and (case_name.endswith(',') or case_name.endswith(' ') or 
                                   case_name.endswith('...') or case_name.rstrip().endswith(',')):
        # Only mark as truncated if ends with comma, space, or ellipsis
        truncated.append(citation_text)
        issues.append("TRUNCATED")
    else:
        good_count += 1
        issues.append("OK")
    
    print(f"   Status: {', '.join(issues)}")
    print()

print(f"{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"Good extractions: {good_count}/{len(citations)} ({good_count/len(citations)*100:.1f}%)")
print(f"N/A extractions: {n_a_count}/{len(citations)} ({n_a_count/len(citations)*100:.1f}%)")
print(f"Truncated: {len(truncated)}")
print(f"Sentence fragments: {len(sentence_fragments)}")
print(f"Signal words: {len(signal_words)}")

# Date extraction
with_dates = sum(1 for c in citations if c.get('extracted_date'))
print(f"\nDate extraction: {with_dates}/{len(citations)} ({with_dates/len(citations)*100:.1f}%)")

# Verification
verified = sum(1 for c in citations if c.get('verified') or c.get('canonical_name'))
print(f"Verified: {verified}/{len(citations)} ({verified/len(citations)*100:.1f}%)")

# Debug: Check what fields exist in first citation
if citations:
    print(f"\nDEBUG: First citation fields: {list(citations[0].keys())}")
    print(f"DEBUG: Sample citation data:")
    sample = citations[0]
    for key in ['verified', 'canonical_name', 'canonical_date', 'canonical_url']:
        if key in sample:
            print(f"  {key}: {sample[key]}")
