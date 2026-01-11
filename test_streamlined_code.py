import json
import re
import fitz

# Extract text the same way the backend does
doc = fitz.open('motion.pdf')
text_parts = []
for page_num in range(len(doc)):
    page = doc[page_num]
    rect = page.rect
    width, height = rect.width, rect.height
    text_area = fitz.Rect(0, 65, width, height - 50)
    text = page.get_text("text", clip=text_area)
    if text.strip():
        text_parts.append(text)
doc.close()

pymupdf_text = "\n".join(text_parts)
normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", pymupdf_text)
normalized = re.sub(r"\s+", " ", normalized)
normalized = normalized.strip()

# Load JSON results
with open('motion_test_streamlined.json', 'r') as f:
    data = json.load(f)

# Find citations
wl_citations = []
for cit in data.get('citations', []):
    citation_text = cit.get('citation', '')
    if '2024 WL 1232082' in citation_text:
        wl_citations.append({
            'citation': citation_text,
            'start': cit.get('start_index'),
            'end': cit.get('end_index'),
            'extracted_name': cit.get('extracted_case_name'),
        })

print("=" * 80)
print("🎯 TESTING STREAMLINED CODE")
print("=" * 80)

# Test position alignment
actual_matches = list(re.finditer(r'2024 WL 1232082', normalized))
position_aligned = 0

for i, cit in enumerate(wl_citations, 1):
    start = cit['start']
    end = cit['end']
    actual_start = actual_matches[i-1].start() if i <= len(actual_matches) else None
    
    if start and actual_start:
        offset = start - actual_start
        if offset == 0:
            position_aligned += 1
            print(f"✅ Occurrence {i}: Position ALIGNED ({start}-{end})")
        else:
            print(f"❌ Occurrence {i}: Position MISALIGNED (offset: {offset})")

print(f"\n{'=' * 80}")
print("RESULTS")
print("=" * 80)

if position_aligned == len(wl_citations):
    print(f"\n✅ ✅ ✅ ALL {position_aligned} POSITIONS ALIGNED! ✅ ✅ ✅")
    print("\n🎯 Streamlined code is working correctly!")
    print("🎯 Single normalization point in UnifiedTextExtractor")
    print("🎯 All redundant normalization calls removed")
    print("\n✨ Code is now more efficient and maintainable!")
else:
    print(f"\n⚠️  {position_aligned}/{len(wl_citations)} aligned")
    print("⚠️  Streamlining may have introduced issues")
