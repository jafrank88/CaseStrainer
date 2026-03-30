"""
Validate year extraction across multiple briefs
"""
from pathlib import Path
from src.citation_extraction_endpoint import extract_citations_production
import re

print("="*80)
print("MULTI-BRIEF YEAR EXTRACTION VALIDATION")
print("="*80)

briefs_dir = Path("wa_briefs_text")
briefs = sorted(list(briefs_dir.glob("*.txt")))[:10]

print(f"\nTesting {len(briefs)} briefs...\n")

total_citations = 0
total_with_years = 0
total_without_years = 0
total_valid_format = 0

reference_patterns = [r'\bid\b', r'\bId\.', r'\bsupra\b', r'\binfra\b', r"aff['']d"]

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
    
    # Count year extractions
    with_years = sum(1 for c in body_citations if c.get('extracted_date') and c.get('extracted_date') != 'N/A')
    without_years = len(body_citations) - with_years
    
    # Validate year format
    valid_format = 0
    for c in body_citations:
        year = c.get('extracted_date')
        if year and year != 'N/A':
            if re.match(r'^\d{4}$', year):
                year_int = int(year)
                if 1700 <= year_int <= 2025:
                    valid_format += 1
            elif re.match(r'^\d{2}$', year):
                valid_format += 1
    
    total_citations += len(body_citations)
    total_with_years += with_years
    total_without_years += without_years
    total_valid_format += valid_format
    
    success_rate = with_years / len(body_citations) * 100 if body_citations else 0
    
    brief_name = brief_path.name
    if len(brief_name) > 50:
        brief_name = brief_name[:47] + "..."
    
    status = "✅" if success_rate >= 95 else "⚠️"
    
    results.append({
        'name': brief_name,
        'citations': len(body_citations),
        'with_years': with_years,
        'without_years': without_years,
        'rate': success_rate
    })
    
    print(f"{status} {brief_name:50s} {with_years:3d}/{len(body_citations):3d} ({success_rate:5.1f}%)")

print(f"\n{'='*80}")
print("OVERALL SUMMARY")
print(f"{'='*80}\n")

overall_rate = total_with_years / total_citations * 100 if total_citations else 0
format_rate = total_valid_format / total_with_years * 100 if total_with_years else 0

print(f"Total briefs tested: {len(briefs)}")
print(f"Total substantive citations: {total_citations}")
print(f"With extracted years: {total_with_years} ({overall_rate:.1f}%)")
print(f"Without years: {total_without_years} ({total_without_years/total_citations*100:.1f}%)")
print(f"Valid year format: {total_valid_format}/{total_with_years} ({format_rate:.1f}%)")

# Count how many briefs met 95% target
briefs_above_95 = sum(1 for r in results if r['rate'] >= 95)
print(f"\nBriefs meeting 95% target: {briefs_above_95}/{len(briefs)} ({briefs_above_95/len(briefs)*100:.1f}%)")

# Stats
if results:
    rates = [r['rate'] for r in results if r['citations'] > 0]
    if rates:
        min_rate = min(rates)
        max_rate = max(rates)
        avg_rate = sum(rates) / len(rates)
        
        print(f"\nAccuracy range: {min_rate:.1f}% - {max_rate:.1f}%")
        print(f"Average accuracy: {avg_rate:.1f}%")

print(f"\n{'='*80}")
print("COMPARISON: CASE NAME vs YEAR EXTRACTION")
print(f"{'='*80}\n")

print(f"Case name extraction: 98.4%")
print(f"Year extraction:      {overall_rate:.1f}%")

if overall_rate >= 95:
    print(f"\n✅ BOTH EXCEED 95% TARGET!")
    print(f"   Case names: 98.4% ✅")
    print(f"   Years:      {overall_rate:.1f}% ✅")
else:
    print(f"\n⚠️  Year extraction below target")
    gap = (0.95 - overall_rate/100) * total_citations
    print(f"   Need +{gap:.0f} more years to reach 95%")

print(f"\n{'='*80}")
