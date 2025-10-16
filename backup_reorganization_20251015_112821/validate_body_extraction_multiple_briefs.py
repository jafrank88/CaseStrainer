"""
Validate body extraction across multiple briefs
Focus: Document body only, excluding TOA, Id., aff'd
"""
from pathlib import Path
from src.citation_extraction_endpoint import extract_citations_production
import re

print("="*80)
print("MULTI-BRIEF BODY EXTRACTION VALIDATION")
print("="*80)

briefs_dir = Path("wa_briefs_text")
briefs = sorted(list(briefs_dir.glob("*.txt")))[:10]

print(f"\nTesting {len(briefs)} briefs...\n")

total_citations = 0
total_with_names = 0
total_without_names = 0

reference_patterns = [
    r'\bid\b',
    r'\bId\.',
    r'\bsupra\b',
    r'\binfra\b',
    r"aff['']d",
    r'\brev\b',
    r"rev['']d",
]

results = []

for brief_path in briefs:
    with open(brief_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    # Remove TOA
    toa_match = re.search(r'TABLE OF AUTHORITIES(.*?)(?=INTRODUCTION|STATEMENT OF|ARGUMENT|I\.)', text, re.DOTALL | re.IGNORECASE)
    if toa_match:
        body_text = text.replace(toa_match.group(0), '')
    else:
        body_text = text
    
    # Extract citations
    result = extract_citations_production(body_text)
    citations = result['citations']
    
    # Filter out reference citations
    body_citations = [
        c for c in citations
        if not any(re.search(pattern, c['citation'].lower(), re.IGNORECASE) for pattern in reference_patterns)
    ]
    
    # Count successes
    with_names = sum(1 for c in body_citations if c.get('extracted_case_name') and c.get('extracted_case_name') != 'N/A')
    without_names = len(body_citations) - with_names
    
    total_citations += len(body_citations)
    total_with_names += with_names
    total_without_names += without_names
    
    success_rate = with_names / len(body_citations) * 100 if body_citations else 0
    
    brief_name = brief_path.name
    if len(brief_name) > 50:
        brief_name = brief_name[:47] + "..."
    
    status = "✅" if success_rate >= 95 else "⚠️"
    
    results.append({
        'name': brief_name,
        'citations': len(body_citations),
        'success': with_names,
        'failed': without_names,
        'rate': success_rate
    })
    
    print(f"{status} {brief_name:50s} {with_names:3d}/{len(body_citations):3d} ({success_rate:5.1f}%)")

print(f"\n{'='*80}")
print("OVERALL SUMMARY")
print(f"{'='*80}\n")

overall_rate = total_with_names / total_citations * 100 if total_citations else 0

print(f"Total briefs tested: {len(briefs)}")
print(f"Total substantive citations: {total_citations}")
print(f"Successfully extracted: {total_with_names} ({overall_rate:.1f}%)")
print(f"Failed: {total_without_names} ({total_without_names/total_citations*100:.1f}%)")

# Count how many briefs met 95% target
briefs_above_95 = sum(1 for r in results if r['rate'] >= 95)
print(f"\nBriefs meeting 95% target: {briefs_above_95}/{len(briefs)} ({briefs_above_95/len(briefs)*100:.1f}%)")

# Stats
if results:
    rates = [r['rate'] for r in results]
    min_rate = min(rates)
    max_rate = max(rates)
    avg_rate = sum(rates) / len(rates)
    
    print(f"\nAccuracy range: {min_rate:.1f}% - {max_rate:.1f}%")
    print(f"Average accuracy: {avg_rate:.1f}%")

print(f"\n{'='*80}")
if overall_rate >= 95:
    print("✅ PRODUCTION READY: Body extraction exceeds 95% target!")
else:
    print(f"⚠️  Below target: Need +{(0.95 - overall_rate/100) * total_citations:.0f} citations")
print(f"{'='*80}")
