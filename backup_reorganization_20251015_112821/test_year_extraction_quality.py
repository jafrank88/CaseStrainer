"""
Test year extraction quality for citations
"""
from pathlib import Path
from src.citation_extraction_endpoint import extract_citations_production
import re

print("="*80)
print("YEAR EXTRACTION QUALITY TEST")
print("="*80)

# Load a real brief
briefs_dir = Path("wa_briefs_text")
brief = briefs_dir / "002_Petition for Review.txt"

with open(brief, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print(f"\nTest document: {brief.name}")
print(f"Length: {len(text):,} characters")

# Remove TOA
toa_match = re.search(r'TABLE OF AUTHORITIES(.*?)(?=INTRODUCTION|STATEMENT OF|ARGUMENT|I\.)', text, re.DOTALL | re.IGNORECASE)
if toa_match:
    body_text = text.replace(toa_match.group(0), '')
    print(f"\n✂️  Removed TOA section")
else:
    body_text = text

# Extract citations
print(f"\n🔧 Extracting citations...")
result = extract_citations_production(body_text)
citations = result['citations']

# Filter out reference citations
reference_patterns = [r'\bid\b', r'\bId\.', r'\bsupra\b', r'\binfra\b', r"aff['']d"]
body_citations = [
    c for c in citations
    if not any(re.search(pattern, c['citation'].lower(), re.IGNORECASE) for pattern in reference_patterns)
]

print(f"✅ Found {len(body_citations)} substantive citations")

# Analyze year extraction
with_years = [c for c in body_citations if c.get('extracted_date') and c.get('extracted_date') != 'N/A']
without_years = [c for c in body_citations if not c.get('extracted_date') or c.get('extracted_date') == 'N/A']

print(f"\n{'='*80}")
print("YEAR EXTRACTION RESULTS")
print(f"{'='*80}")

print(f"\n✅ With years: {len(with_years)}/{len(body_citations)} ({len(with_years)/len(body_citations)*100:.1f}%)")
print(f"❌ Without years: {len(without_years)}/{len(body_citations)} ({len(without_years)/len(body_citations)*100:.1f}%)")

# Show examples of successful year extractions
if with_years:
    print(f"\n{'='*80}")
    print("✅ SUCCESSFUL YEAR EXTRACTIONS (Examples)")
    print(f"{'='*80}\n")
    for cite in with_years[:15]:
        print(f"  {cite['citation']:30s} → Year: {cite['extracted_date']:6s}   Case: {cite.get('extracted_case_name', 'N/A')[:40]}")

# Show examples of failures
if without_years:
    print(f"\n{'='*80}")
    print("❌ FAILED YEAR EXTRACTIONS")
    print(f"{'='*80}\n")
    
    for i, cite in enumerate(without_years[:15], 1):
        citation_text = cite['citation']
        case_name = cite.get('extracted_case_name', 'N/A')
        
        # Find in text to see if there's a year nearby
        pattern = re.escape(citation_text)
        match = re.search(pattern, body_text, re.IGNORECASE)
        
        if match:
            start = max(0, match.start() - 50)
            end = min(len(body_text), match.end() + 100)
            context = body_text[start:end]
            context = ' '.join(context.split())
            
            # Look for year pattern in context
            year_pattern = r'\((\d{4})\)'
            year_matches = re.findall(year_pattern, context)
            
            print(f"{i}. {citation_text}")
            print(f"   Case: {case_name[:60]}")
            if year_matches:
                print(f"   ⚠️  Year nearby: {year_matches}")
            print(f"   Context: ...{context[:150]}...")
            print()

# Validate year format
print(f"\n{'='*80}")
print("YEAR FORMAT VALIDATION")
print(f"{'='*80}\n")

valid_years = 0
invalid_years = 0
year_formats = {'4-digit': 0, '2-digit': 0, 'invalid': 0}

for cite in with_years:
    year = cite['extracted_date']
    
    if re.match(r'^\d{4}$', year):
        year_formats['4-digit'] += 1
        year_int = int(year)
        if 1700 <= year_int <= 2025:
            valid_years += 1
        else:
            invalid_years += 1
            print(f"⚠️  Invalid year range: {year} for {cite['citation']}")
    elif re.match(r'^\d{2}$', year):
        year_formats['2-digit'] += 1
        valid_years += 1
    else:
        year_formats['invalid'] += 1
        invalid_years += 1
        print(f"⚠️  Invalid year format: '{year}' for {cite['citation']}")

print(f"Valid years: {valid_years}/{len(with_years)} ({valid_years/len(with_years)*100:.1f}%)")
print(f"Invalid years: {invalid_years}/{len(with_years)} ({invalid_years/len(with_years)*100:.1f}%)")
print(f"\nYear formats:")
for fmt, count in year_formats.items():
    print(f"  {fmt}: {count}")

print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")

print(f"""
Year extraction from body text:
  - Total substantive citations: {len(body_citations)}
  - With extracted years: {len(with_years)} ({len(with_years)/len(body_citations)*100:.1f}%)
  - Without years: {len(without_years)} ({len(without_years)/len(body_citations)*100:.1f}%)
  - Valid year format: {valid_years}/{len(with_years)} ({valid_years/len(with_years)*100:.1f}% of extracted)

Target: 95%+ year extraction accuracy
Current: {len(with_years)/len(body_citations)*100:.1f}%
""")

if len(with_years)/len(body_citations) >= 0.95:
    print("✅ TARGET ACHIEVED! 95%+ year extraction accuracy")
else:
    gap = 0.95 - (len(with_years)/len(body_citations))
    needed = int(gap * len(body_citations))
    print(f"⚠️  Need to improve {needed} more citations to reach 95%")

print("="*80)
