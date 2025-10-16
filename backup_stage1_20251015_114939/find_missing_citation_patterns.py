"""
Find citation patterns we're missing by comparing against CourtListener
"""

import requests
import time
from src.config import COURTLISTENER_API_KEY
from src.citation_extraction_endpoint import extract_citations_with_clustering

print("="*80)
print("FINDING MISSING CITATION PATTERNS")
print("="*80)

if not COURTLISTENER_API_KEY:
    print("ERROR: No CourtListener API key found!")
    exit(1)

headers = {
    'Authorization': f'Token {COURTLISTENER_API_KEY}',
    'Accept': 'application/json'
}

# Step 1: Search for recent opinions with good text
print(f"\n1. Searching for recent opinions with plain text...")

search_url = "https://www.courtlistener.com/api/rest/v4/search/"
params = {
    'type': 'o',  # opinions
    'order_by': 'dateFiled desc',
    'stat_Precedential': 'Published',  # Published opinions tend to have more citations
}

response = requests.get(search_url, headers=headers, params=params, timeout=30)
print(f"   Status: {response.status_code}")

if response.status_code != 200:
    print(f"   Error: {response.text[:500]}")
    exit(1)

data = response.json()
results = data.get('results', [])
print(f"   Found {len(results)} opinions")

# Track results
all_findings = []
missing_patterns = {}

# Step 2: Process each opinion
for i, result in enumerate(results[:10], 1):  # Test first 10
    case_name = result.get('caseName', 'N/A')
    
    # Extract opinion ID from different possible fields
    opinion_id = result.get('id') or result.get('opinion_id')
    
    # If not found, try to extract from absolute_url
    if not opinion_id and 'absolute_url' in result:
        import re
        match = re.search(r'/opinion/(\d+)/', result['absolute_url'])
        if match:
            opinion_id = match.group(1)
    
    date_filed = result.get('dateFiled', 'N/A')
    court = result.get('court', 'N/A')
    
    print(f"\n{'-'*80}")
    print(f"Case {i}/10: {case_name}")
    print(f"  Court: {court}")
    print(f"  Date: {date_filed}")
    print(f"  Opinion ID: {opinion_id}")
    print(f"  Available fields: {list(result.keys())[:10]}")
    
    # Get the full opinion text
    opinion_url = f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/"
    try:
        op_response = requests.get(opinion_url, headers=headers, timeout=30)
        if op_response.status_code != 200:
            print(f"  [X] Could not fetch opinion")
            continue
        
        op_data = op_response.json()
        opinion_text = op_data.get('plain_text', '')
        
        if not opinion_text or len(opinion_text) < 100:
            print(f"  [X] No usable text (only {len(opinion_text)} chars)")
            continue
        
        print(f"  [OK] Got opinion text: {len(opinion_text):,} chars")
        
        # Step 3: Ask CourtListener what citations are in this text
        print(f"  -> Asking CourtListener to extract citations...")
        
        # Use citation-lookup API to parse the text
        lookup_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        lookup_payload = {"text": opinion_text[:50000]}  # Limit to 50k chars for API
        
        time.sleep(0.5)  # Rate limiting
        lookup_response = requests.post(lookup_url, json=lookup_payload, headers=headers, timeout=60)
        
        if lookup_response.status_code != 200:
            print(f"  [X] Citation lookup failed: {lookup_response.status_code}")
            continue
        
        cl_citations_data = lookup_response.json()
        
        # Extract unique citations found by CourtListener
        cl_citations = set()
        if isinstance(cl_citations_data, list):
            for item in cl_citations_data:
                if isinstance(item, dict) and 'citation' in item:
                    cl_citations.add(item['citation'])
        
        print(f"  [OK] CourtListener found {len(cl_citations)} citations")
        
        # Step 4: Run OUR extraction on the same text
        print(f"  -> Running our extraction pipeline...")
        
        try:
            our_result = extract_citations_with_clustering(opinion_text, enable_verification=False)
            our_citations_list = our_result.get('citations', [])
            our_citations = set(c.get('citation', '') for c in our_citations_list)
            
            print(f"  [OK] We found {len(our_citations)} citations")
            
            # Step 5: Compare
            missing = cl_citations - our_citations
            extra = our_citations - cl_citations
            matched = cl_citations & our_citations
            
            print(f"\n  COMPARISON:")
            print(f"    Matched: {len(matched)}")
            print(f"    Missing (we didn't find): {len(missing)}")
            print(f"    Extra (we found, they didn't): {len(extra)}")
            
            if missing:
                print(f"\n  [!] MISSING CITATIONS:")
                for cit in sorted(missing)[:10]:
                    print(f"      - {cit}")
                    
                    # Categorize by pattern
                    if '-' in cit and any(state in cit for state in ['Ohio', 'Cal', 'Ill', 'Tex', 'Fla', 'N.Y']):
                        pattern_type = 'dash-separated-state'
                    elif 'U.S.' in cit:
                        pattern_type = 'us-reports'
                    elif 'F.' in cit:
                        pattern_type = 'federal'
                    elif 'WL' in cit:
                        pattern_type = 'westlaw'
                    else:
                        pattern_type = 'other'
                    
                    missing_patterns[pattern_type] = missing_patterns.get(pattern_type, []) + [cit]
            
            all_findings.append({
                'case_name': case_name,
                'cl_count': len(cl_citations),
                'our_count': len(our_citations),
                'matched': len(matched),
                'missing': len(missing),
                'extra': len(extra),
                'missing_citations': list(missing)[:10]
            })
            
        except Exception as e:
            print(f"  [X] Our extraction failed: {e}")
            continue
        
    except Exception as e:
        print(f"  [X] Error: {e}")
        continue

# Step 6: Summary
print(f"\n\n{'='*80}")
print(f"SUMMARY - PATTERN GAPS ANALYSIS")
print(f"{'='*80}")

print(f"\nCases analyzed: {len(all_findings)}")

total_cl = sum(f['cl_count'] for f in all_findings)
total_ours = sum(f['our_count'] for f in all_findings)
total_matched = sum(f['matched'] for f in all_findings)
total_missing = sum(f['missing'] for f in all_findings)

print(f"\nOverall Statistics:")
print(f"  CourtListener found: {total_cl} citations")
print(f"  We found: {total_ours} citations")
print(f"  Matched: {total_matched} citations")
print(f"  Missing: {total_missing} citations")
print(f"  Match rate: {(total_matched/total_cl*100) if total_cl > 0 else 0:.1f}%")

print(f"\nMissing Patterns by Type:")
for pattern_type, citations in sorted(missing_patterns.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n  {pattern_type}: {len(citations)} citations")
    for cit in citations[:5]:
        print(f"    - {cit}")

# Save detailed results
import json
with open('missing_citations_analysis.json', 'w') as f:
    json.dump({
        'summary': {
            'cases_analyzed': len(all_findings),
            'total_cl_citations': total_cl,
            'total_our_citations': total_ours,
            'total_matched': total_matched,
            'total_missing': total_missing,
            'match_rate': (total_matched/total_cl*100) if total_cl > 0 else 0
        },
        'missing_patterns': {k: v[:20] for k, v in missing_patterns.items()},
        'detailed_findings': all_findings
    }, f, indent=2)

print(f"\n[OK] Detailed results saved to: missing_citations_analysis.json")
print(f"\n{'='*80}")
