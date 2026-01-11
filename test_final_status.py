import json
import PyPDF2
import re

# Load the latest JSON results
with open('motion_test_cache_cleared.json', 'r') as f:
    data = json.load(f)

# Extract and normalize text from PDF
with open('motion.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    original_text = ""
    for page in pdf_reader.pages:
        original_text += page.extract_text()

# Normalize text
normalized_text = re.sub(r"\s+", " ", original_text)

print("=" * 80)
print("FINAL STATUS REPORT")
print("=" * 80)

print(f"\nText lengths:")
print(f"  Original PDF text: {len(original_text)} chars")
print(f"  Normalized text: {len(normalized_text)} chars")
print(f"  Difference: {len(original_text) - len(normalized_text)} chars removed by normalization")

# Find citations in JSON
wl_citations = []
for cit in data.get('citations', []):
    citation_text = cit.get('citation', '')
    if '2024 WL 1232082' in citation_text:
        wl_citations.append({
            'citation': citation_text,
            'start': cit.get('start_index'),
            'end': cit.get('end_index'),
            'extracted_name': cit.get('extracted_case_name'),
            'cluster_id': cit.get('cluster_id')
        })

print(f"\nFound {len(wl_citations)} occurrences of '2024 WL 1232082'")

# Find actual positions
actual_matches = list(re.finditer(r'2024 WL 1232082', normalized_text))
print(f"Actual positions in normalized text: {len(actual_matches)}")

print(f"\n{'=' * 80}")
print("POSITION ALIGNMENT CHECK")
print("=" * 80)

for i, cit in enumerate(wl_citations, 1):
    start = cit['start']
    end = cit['end']
    actual_start = actual_matches[i-1].start() if i <= len(actual_matches) else None
    
    print(f"\nOccurrence {i}:")
    print(f"  JSON position: {start}-{end}")
    print(f"  Actual position: {actual_start}-{actual_matches[i-1].end() if i <= len(actual_matches) else None}")
    print(f"  Position offset: {start - actual_start if start and actual_start else 'N/A'} chars")
    print(f"  Extracted name: {cit['extracted_name'][:60]}...")
    
    if start is not None and end is not None:
        text_at_pos = normalized_text[start:end]
        
        if '2024 WL 1232082' in text_at_pos:
            print(f"  ✅ ALIGNED")
        else:
            print(f"  ❌ MISALIGNED - Text at position: '{text_at_pos}'")

print(f"\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)

print("\n✅ Completed:")
print("  - Added text normalization at 7 extraction points")
print("  - Added semicolon boundary detection")
print("  - Cleared Redis cache")
print("  - Restarted all services")

print("\n❌ Issue:")
print("  - Position misalignment persists (~44 chars off)")
print("  - Text is 12915 chars when it should be 13030 chars before eyecite")
print("  - File processing through async/queued path bypassing normalization")

print("\n🔍 Root Cause:")
print("  - Text extraction happens through a code path where positions are set")
print("    BEFORE text normalization occurs")
print("  - The 12915 char text indicates partial normalization is happening")
print("    somewhere before my normalization code runs")

print("\n📋 Next Steps:")
print("  1. Identify which extraction library is actually being used (fitz/pdfplumber/pypdf)")
print("  2. Find where the 12915-char text is coming from")
print("  3. Ensure normalization happens at the absolute first point of text entry")
print("  4. Consider forcing synchronous processing for testing")
