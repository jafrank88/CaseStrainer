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

# Normalize
normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", pymupdf_text)
normalized = re.sub(r"\s+", " ", normalized)
normalized = normalized.strip()

# Load JSON results
with open('motion_test_final_norm.json', 'r') as f:
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
print("🎯 CASE NAME EXTRACTION & SEMICOLON BOUNDARY TEST")
print("=" * 80)

print(f"\nFound {len(wl_citations)} occurrences of '2024 WL 1232082'")

for i, cit in enumerate(wl_citations, 1):
    start = cit['start']
    end = cit['end']
    
    print(f"\n{'=' * 80}")
    print(f"Occurrence {i}: Position {start}-{end}")
    print(f"{'=' * 80}")
    
    # Show context before citation
    context_start = max(0, start - 300)
    context = normalized[context_start:start]
    
    print(f"\nContext before citation (last 300 chars):")
    print(f"'{context[-200:]}'")
    
    # Check for semicolon
    if ';' in context:
        last_semi = context.rfind(';')
        text_after_semi = context[last_semi+1:].strip()
        print(f"\n✅ Semicolon found at position {context_start + last_semi}")
        print(f"Text after last semicolon: '{text_after_semi}'")
        
        # Check if case name should be from text after semicolon
        if 'Doe v. Teachers Council' in text_after_semi:
            print(f"✅ Expected case name 'Doe v. Teachers Council' found after semicolon")
        elif 'Schiller' in context[:last_semi]:
            print(f"⚠️  'Schiller' appears BEFORE the semicolon (should not contaminate)")
    else:
        print(f"\n⚠️  No semicolon found in context")
    
    print(f"\nExtracted case name: '{cit['extracted_name']}'")
    
    # Verify correctness
    if 'Doe v. Teachers Council' in cit['extracted_name']:
        print(f"✅ CORRECT CASE NAME!")
    elif 'Schiller' in cit['extracted_name']:
        print(f"❌ WRONG - Schiller contamination (semicolon boundary NOT working)")
        print(f"   This means the semicolon boundary detection failed")
    else:
        print(f"⚠️  Other case name extracted")

print(f"\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)

correct_count = sum(1 for c in wl_citations if 'Doe v. Teachers Council' in c['extracted_name'])
schiller_count = sum(1 for c in wl_citations if 'Schiller' in c['extracted_name'])

print(f"\nCorrect extractions: {correct_count}/{len(wl_citations)}")
print(f"Schiller contaminations: {schiller_count}/{len(wl_citations)}")

if correct_count == len(wl_citations):
    print(f"\n✅ ✅ ✅ ALL CASE NAMES CORRECT! ✅ ✅ ✅")
    print("\n🎯 Position alignment: WORKING")
    print("🎯 Semicolon boundary detection: WORKING")
    print("🎯 Case name extraction: CORRECT")
    print("\n🎉 🎉 🎉 COMPLETE SUCCESS! 🎉 🎉 🎉")
else:
    print(f"\n⚠️  {correct_count}/{len(wl_citations)} correct")
    if schiller_count > 0:
        print(f"❌ Semicolon boundary detection NOT working")
        print(f"   Need to debug case name extraction logic")
    else:
        print(f"⚠️  Case names extracted but not matching expected")

# Check clustering
if len(wl_citations) >= 2:
    print(f"\nClustering:")
    for i, cit in enumerate(wl_citations, 1):
        print(f"  Occurrence {i}: Cluster {cit['cluster_id']}")
    
    if wl_citations[0]['cluster_id'] != wl_citations[1]['cluster_id']:
        print(f"\n✅ Different clusters (correct if different case names)")
    elif wl_citations[0]['cluster_id'] is None:
        print(f"\n⚠️  No clustering applied")
    else:
        print(f"\n⚠️  Same cluster (may indicate clustering issue)")
