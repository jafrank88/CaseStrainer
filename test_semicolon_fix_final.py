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
with open('motion_test_semicolon_fix.json', 'r') as f:
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
            'cluster_id': cit.get('cluster_id')
        })

print("=" * 80)
print("🎉 FINAL TEST: POSITION ALIGNMENT + SEMICOLON BOUNDARY DETECTION")
print("=" * 80)

print(f"\nFound {len(wl_citations)} occurrences of '2024 WL 1232082'")

# Test position alignment
actual_matches = list(re.finditer(r'2024 WL 1232082', normalized))
position_aligned = 0
correct_names = 0

for i, cit in enumerate(wl_citations, 1):
    start = cit['start']
    end = cit['end']
    actual_start = actual_matches[i-1].start() if i <= len(actual_matches) else None
    
    print(f"\n{'=' * 80}")
    print(f"Occurrence {i}")
    print(f"{'=' * 80}")
    
    # Check position alignment
    if start and actual_start:
        offset = start - actual_start
        if offset == 0:
            print(f"✅ Position ALIGNED: {start}-{end}")
            position_aligned += 1
        else:
            print(f"❌ Position MISALIGNED: JSON {start} vs Actual {actual_start} (offset: {offset})")
    
    # Check case name
    print(f"Extracted name: '{cit['extracted_name']}'")
    
    if 'Doe v. Teachers Council' in cit['extracted_name']:
        print(f"✅ CORRECT CASE NAME!")
        correct_names += 1
    elif 'Schiller' in cit['extracted_name']:
        print(f"❌ WRONG - Schiller contamination")
    else:
        print(f"⚠️  Other name")

print(f"\n{'=' * 80}")
print("🎉 FINAL RESULTS")
print("=" * 80)

print(f"\n📊 Position Alignment: {position_aligned}/{len(wl_citations)}")
print(f"📊 Correct Case Names: {correct_names}/{len(wl_citations)}")

if position_aligned == len(wl_citations):
    print(f"\n✅ ✅ ✅ ALL POSITIONS ALIGNED! ✅ ✅ ✅")
    print("🎯 Sync/async position alignment issue: RESOLVED")
else:
    print(f"\n⚠️  Position alignment incomplete")

if correct_names == len(wl_citations):
    print(f"\n✅ ✅ ✅ ALL CASE NAMES CORRECT! ✅ ✅ ✅")
    print("🎯 Semicolon boundary detection: WORKING")
else:
    print(f"\n⚠️  Case name extraction incomplete")

if position_aligned == len(wl_citations) and correct_names == len(wl_citations):
    print(f"\n🎉 🎉 🎉 COMPLETE SUCCESS! 🎉 🎉 🎉")
    print("\n✅ Position alignment: FIXED")
    print("✅ Text normalization: WORKING")
    print("✅ Semicolon boundary detection: WORKING")
    print("✅ Case name extraction: CORRECT")
    print("\n🎯 All sync/async position misalignment issues RESOLVED!")

# Check clustering
if len(wl_citations) >= 2:
    print(f"\nClustering:")
    for i, cit in enumerate(wl_citations, 1):
        print(f"  Occurrence {i}: Cluster {cit['cluster_id']}")
    
    if wl_citations[0]['cluster_id'] != wl_citations[1]['cluster_id']:
        print(f"\n✅ Different clusters (correct - different case names)")
