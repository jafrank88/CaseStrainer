"""
Diagnose why only 37/62 citations are being found.
Compare eyecite + regex results to understand what's missing.
"""

import PyPDF2
import re
from eyecite import get_citations

# Extract text
pdf_path = r"D:\dev\casestrainer\24-2626.pdf"
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

print(f"Text length: {len(text)} characters\n")

# Try eyecite
print("="*80)
print("EYECITE EXTRACTION")
print("="*80)
eyecite_citations = list(get_citations(text))
print(f"Found {len(eyecite_citations)} citations\n")

# Show first 10
for idx, cit in enumerate(eyecite_citations[:10], 1):
    print(f"{idx}. {cit}")

# Try regex patterns from clean_extraction_pipeline
print("\n" + "="*80)
print("REGEX PATTERN EXTRACTION")
print("="*80)

patterns = {
    'us_supreme': re.compile(r'\b\d+\s+U\.S\.\s+\d+\b', re.IGNORECASE),
    's_ct': re.compile(r'\b\d+\s+S\.\s*Ct\.\s+\d+\b', re.IGNORECASE),
    'l_ed': re.compile(r'\b\d+\s+L\.\s*Ed\.?\s*2d\s+\d+\b', re.IGNORECASE),
    'f_2d': re.compile(r'\b\d+\s+F\.\s*2d\s+\d+\b', re.IGNORECASE),
    'f_3d': re.compile(r'\b\d+\s+F\.\s*3d\s+\d+\b', re.IGNORECASE),
    'f_4th': re.compile(r'\b\d+\s+F\.\s*4th\s+\d+\b', re.IGNORECASE),
    'wn_2d': re.compile(r'\b\d+\s+Wn\.2d\s+\d+\b', re.IGNORECASE),
    'wn_app': re.compile(r'\b\d+\s+Wn\.\s*App\.?\s*2d\s+\d+\b', re.IGNORECASE),
    'p_2d': re.compile(r'\b\d+\s+P\.\s*2d\s+\d+\b', re.IGNORECASE),
    'p_3d': re.compile(r'\b\d+\s+P\.\s*3d\s+\d+\b', re.IGNORECASE),
}

all_regex_matches = []
for pattern_name, pattern in patterns.items():
    matches = list(pattern.finditer(text))
    print(f"{pattern_name}: {len(matches)} matches")
    all_regex_matches.extend([(m.group(0), m.start()) for m in matches])

# Deduplicate
seen = set()
unique_regex = []
for cit_text, start in all_regex_matches:
    key = (cit_text, start // 10)  # Same bucketing as clean_extraction_pipeline
    if key not in seen:
        unique_regex.append((cit_text, start))
        seen.add(key)

print(f"\nTotal unique regex matches: {len(unique_regex)}")

# Combined total
combined = set()
for cit in eyecite_citations:
    combined.add(str(cit).strip())
for cit_text, start in unique_regex:
    combined.add(cit_text.strip())

print(f"\n" + "="*80)
print(f"COMBINED TOTAL: {len(combined)} unique citations")
print("="*80)

# Show some examples
print("\nSample citations (first 20):")
for idx, cit in enumerate(sorted(combined)[:20], 1):
    print(f"{idx}. {cit}")
