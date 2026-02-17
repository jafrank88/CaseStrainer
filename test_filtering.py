"""Test script to trace citation filtering."""
import sys
sys.path.insert(0, 'src')

from robust_pdf_extractor import RobustPDFExtractor
from utils.text_normalizer import normalize_text
from eyecite import get_citations
import re

print("=" * 60)
print("CITATION FILTERING TRACE")
print("=" * 60)

# Extract text
extractor = RobustPDFExtractor()
result = extractor.extract_text('20-297_4g25.pdf')
text = result[0] if isinstance(result, tuple) else result
print(f"\n1. RAW TEXT: {len(text)} chars")

# Normalize
normalized = normalize_text(text)
print(f"2. NORMALIZED: {len(normalized)} chars")

# Get all eyecite citations
all_cites = get_citations(normalized)
print(f"3. EYECITE FOUND: {len(all_cites)} citations")

# Count by type
from collections import Counter
types = Counter(str(type(c).__name__) for c in all_cites)
print("\n   By type:")
for t, count in sorted(types.items(), key=lambda x: -x[1]):
    print(f"     {t}: {count}")

# Simulate the filtering in _extract_citation_text_from_eyecite
print("\n4. FILTERING BY EYECITE TYPE:")
kept_by_eyecite = []
for c in all_cites:
    cit_str = str(c)
    obj_type = type(c).__name__
    
    # Skip non-case citations by type
    if obj_type in ['IdCitation', 'SupraCitation', 'InfraCitation', 'ShortCaseCitation', 'UnknownCitation', 'FullLawCitation']:
        continue
    
    # Filter out statutes
    if any(pattern in cit_str for pattern in ['Stat.', 'U.S.C.', 'C.F.R.', 'Fed. Reg.']):
        continue
    
    # Filter "at" citations
    if ' at ' in cit_str:
        continue
        
    kept_by_eyecite.append(c)

print(f"   After eyecite type/text filtering: {len(kept_by_eyecite)} citations")

# Simulate _deduplicate_citations filtering
print("\n5. CHECKING FOR DEDUPLICATION:")
seen = set()
unique_citations = []
for c in kept_by_eyecite:
    # Extract citation text
    match = re.search(r"FullCaseCitation\('([^']+)'", str(c))
    if match:
        cit_text = match.group(1)
        if cit_text not in seen:
            seen.add(cit_text)
            unique_citations.append(c)
        else:
            print(f"   DUPLICATE: {cit_text}")

print(f"   After deduplication: {len(unique_citations)} citations")

# Check for law review filtering
print("\n6. LAW REVIEW FILTER:")
from citation_extractor import is_law_review_citation
non_law_review = []
for c in unique_citations:
    match = re.search(r"FullCaseCitation\('([^']+)'", str(c))
    if match:
        cit_text = match.group(1)
        if not is_law_review_citation(cit_text):
            non_law_review.append(c)
        else:
            print(f"   LAW REVIEW: {cit_text}")

print(f"   After law review filter: {len(non_law_review)} citations")

# Show sample of what made it through
print("\n7. FINAL CITATIONS (sample):")
for i, c in enumerate(non_law_review[:10]):
    match = re.search(r"FullCaseCitation\('([^']+)'", str(c))
    if match:
        print(f"   {i+1}. {match.group(1)}")

print("\n" + "=" * 60)
print(f"SUMMARY: {len(all_cites)} → {len(kept_by_eyecite)} → {len(unique_citations)} → {len(non_law_review)}")
print("=" * 60)
