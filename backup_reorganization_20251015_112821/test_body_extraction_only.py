"""
Test case name extraction in document body (no TOA, ignore Id./aff'd)
Focus: Extract case names that appear with citations in the document text
"""
from pathlib import Path
from src.citation_extraction_endpoint import extract_citations_production
import re

print("="*80)
print("DOCUMENT BODY CASE NAME EXTRACTION TEST")
print("Excluding: Table of Authorities, Id., aff'd citations")
print("="*80)

# Load a real brief
briefs_dir = Path("wa_briefs_text")
brief = briefs_dir / "002_Petition for Review.txt"

with open(brief, 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print(f"\nTest document: {brief.name}")
print(f"Length: {len(text):,} characters")

# Remove Table of Authorities section
toa_match = re.search(r'TABLE OF AUTHORITIES(.*?)(?=INTRODUCTION|STATEMENT OF|ARGUMENT|I\.)', text, re.DOTALL | re.IGNORECASE)
if toa_match:
    toa_section = toa_match.group(0)
    body_text = text.replace(toa_section, '')
    print(f"\n✂️  Removed TOA section ({len(toa_section):,} chars)")
    print(f"📄 Body text: {len(body_text):,} characters")
else:
    body_text = text
    print(f"\n📄 No TOA found, using full text")

# Extract from body
print(f"\n🔧 Extracting citations from body text...")
result = extract_citations_production(body_text)
citations = result['citations']

print(f"✅ Found {len(citations)} citations")

# Filter out Id., aff'd, supra, etc.
reference_patterns = [
    r'\bid\b',
    r'\bId\.',
    r'\bsupra\b',
    r'\binfra\b',
    r"aff['']d",
    r'\brev\b',
    r"rev['']d",
]

body_citations = []
for cite in citations:
    citation_text = cite['citation'].lower()
    # Skip if it's a reference citation
    if any(re.search(pattern, citation_text, re.IGNORECASE) for pattern in reference_patterns):
        continue
    body_citations.append(cite)

print(f"📊 After filtering references: {len(body_citations)} substantive citations")

# Analyze success rate
with_names = [c for c in body_citations if c.get('extracted_case_name') and c.get('extracted_case_name') != 'N/A']
without_names = [c for c in body_citations if not c.get('extracted_case_name') or c.get('extracted_case_name') == 'N/A']

print(f"\n{'='*80}")
print("RESULTS")
print(f"{'='*80}")

print(f"\n✅ With case names: {len(with_names)}/{len(body_citations)} ({len(with_names)/len(body_citations)*100:.1f}%)")
print(f"❌ Without case names: {len(without_names)}/{len(body_citations)} ({len(without_names)/len(body_citations)*100:.1f}%)")

# Show examples of successful extractions
if with_names:
    print(f"\n{'='*80}")
    print("✅ SUCCESSFUL EXTRACTIONS (Examples)")
    print(f"{'='*80}\n")
    for cite in with_names[:10]:
        propagated = " [PROPAGATED]" if cite.get('propagated_from_parallel') else ""
        print(f"  {cite['citation']}")
        print(f"    → {cite['extracted_case_name']}{propagated}")
        print()

# Show examples of failures
if without_names:
    print(f"\n{'='*80}")
    print("❌ FAILED EXTRACTIONS")
    print(f"{'='*80}\n")
    
    # Find context for each failure
    for i, cite in enumerate(without_names[:10], 1):
        citation_text = cite['citation']
        
        # Find in text
        pattern = re.escape(citation_text)
        match = re.search(pattern, body_text, re.IGNORECASE)
        
        if match:
            start = max(0, match.start() - 150)
            end = min(len(body_text), match.end() + 50)
            context = body_text[start:end]
            context = ' '.join(context.split())
            
            print(f"{i}. {citation_text}")
            print(f"   Context: ...{context}...")
            
            # Check if there's a case name nearby
            before_cite = body_text[max(0, match.start()-300):match.start()]
            if ' v. ' in before_cite or ' v ' in before_cite:
                # Find the last occurrence of v.
                v_matches = list(re.finditer(r'([A-Z][A-Za-z\s,\.&]+)\s+v\.?\s+([A-Z][A-Za-z\s,\.&]+)', before_cite))
                if v_matches:
                    last_match = v_matches[-1]
                    potential_name = last_match.group(0)
                    print(f"   ⚠️  Potential name nearby: '{potential_name}'")
            print()

print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")

print(f"""
Document body extraction (excluding TOA, Id., aff'd):
  - Total substantive citations: {len(body_citations)}
  - Successfully extracted: {len(with_names)} ({len(with_names)/len(body_citations)*100:.1f}%)
  - Failed: {len(without_names)} ({len(without_names)/len(body_citations)*100:.1f}%)

Target: 95%+ extraction accuracy for body text
Current: {len(with_names)/len(body_citations)*100:.1f}%
""")

if len(with_names)/len(body_citations) >= 0.95:
    print("✅ TARGET ACHIEVED! 95%+ extraction accuracy")
else:
    gap = 0.95 - (len(with_names)/len(body_citations))
    needed = int(gap * len(body_citations))
    print(f"⚠️  Need to improve {needed} more citations to reach 95%")

print("="*80)
