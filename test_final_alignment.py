import json
import PyPDF2
import re

# Load the JSON results
with open('motion_test_final_norm.json', 'r') as f:
    data = json.load(f)

# Extract and normalize text from PDF (same way backend does now)
with open('motion.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    original_text = ""
    for page in pdf_reader.pages:
        original_text += page.extract_text()

# Normalize text the EXACT same way the backend does
# Step 1: Remove problematic characters
normalized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", original_text)
# Step 2: Collapse all whitespace
normalized = re.sub(r"\s+", " ", normalized)
# Step 3: Strip
normalized = normalized.strip()

print("=" * 80)
print("🎯 FINAL POSITION ALIGNMENT TEST")
print("=" * 80)

print(f"\nText lengths:")
print(f"  Original PDF: {len(original_text)} chars")
print(f"  Normalized (our test): {len(normalized)} chars")
print(f"  Backend text (from logs): 12934 chars")
print(f"  Match: {'✅ YES' if len(normalized) == 12934 else '❌ NO'}")

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

print(f"\nFound {len(wl_citations)} occurrences of '2024 WL 1232082' in JSON")

# Find actual positions
actual_matches = list(re.finditer(r'2024 WL 1232082', normalized))
print(f"Actual positions in normalized text: {len(actual_matches)}")

for i, match in enumerate(actual_matches, 1):
    print(f"  Actual {i}: Position {match.start()}-{match.end()}")

print(f"\n{'=' * 80}")
print("POSITION ALIGNMENT CHECK")
print("=" * 80)

success_count = 0
correct_names = 0

for i, cit in enumerate(wl_citations, 1):
    start = cit['start']
    end = cit['end']
    actual_start = actual_matches[i-1].start() if i <= len(actual_matches) else None
    
    print(f"\nOccurrence {i}:")
    print(f"  JSON position: {start}-{end}")
    print(f"  Actual position: {actual_start}-{actual_matches[i-1].end() if i <= len(actual_matches) else None}")
    if start and actual_start:
        offset = start - actual_start
        print(f"  Offset: {offset} chars {'✅ ALIGNED!' if offset == 0 else '❌'}")
    print(f"  Extracted name: {cit['extracted_name'][:60]}...")
    
    if start is not None and end is not None:
        text_at_pos = normalized[start:end]
        
        if '2024 WL 1232082' in text_at_pos:
            print(f"  ✅ POSITION ALIGNED!")
            success_count += 1
            
            # Show context for semicolon check
            context_start = max(0, start - 200)
            context = normalized[context_start:start]
            
            # Check for semicolon
            if ';' in context:
                last_semi = context.rfind(';')
                text_after_semi = context[last_semi+1:].strip()
                print(f"  ✅ Semicolon found before citation")
                print(f"  Text after semicolon: '{text_after_semi[:50]}...'")
            
            # Check case name
            if 'Doe v. Teachers Council' in cit['extracted_name']:
                print(f"  ✅ CORRECT CASE NAME!")
                correct_names += 1
            elif 'Schiller' in cit['extracted_name']:
                print(f"  ❌ WRONG - Schiller contamination (semicolon boundary not working)")
            else:
                print(f"  ⚠️  Other name")
        else:
            print(f"  ❌ MISALIGNED - Text at position: '{text_at_pos}'")

print(f"\n{'=' * 80}")
print("🎉 FINAL RESULTS")
print("=" * 80)

if success_count == len(wl_citations):
    print(f"\n✅ ✅ ✅ ALL {success_count} POSITIONS ALIGNED! ✅ ✅ ✅")
    print("\n🎯 Position pointers are now set AFTER normalization!")
    print("🎯 Eyecite positions match the normalized text!")
    print("🎯 Sync/async position alignment issue RESOLVED!")
    
    if correct_names == len(wl_citations):
        print(f"\n✅ ✅ ✅ ALL {correct_names} CASE NAMES CORRECT! ✅ ✅ ✅")
        print("\n🎯 Semicolon boundary detection is working!")
        print("\n🎉 🎉 🎉 COMPLETE SUCCESS! 🎉 🎉 🎉")
        print("\n✅ Position alignment fix: COMPLETE")
        print("✅ Semicolon boundary detection: WORKING")
        print("✅ Case name extraction: CORRECT")
    else:
        print(f"\n⚠️  {correct_names}/{len(wl_citations)} case names correct")
        print("⚠️  Semicolon boundary detection may need adjustment")
else:
    print(f"\n⚠️  {success_count}/{len(wl_citations)} positions aligned")
    print("⚠️  Still have position misalignment issues")

# Check clustering
if len(wl_citations) >= 2:
    print(f"\nClustering:")
    for i, cit in enumerate(wl_citations, 1):
        print(f"  Occurrence {i}: Cluster {cit['cluster_id']}")
    
    if wl_citations[0]['cluster_id'] != wl_citations[1]['cluster_id']:
        print(f"\n✅ Different clusters (correct - different case names)")
    else:
        print(f"\n⚠️  Same cluster (may need clustering fix)")
