import json
import PyPDF2
import re

# Load the JSON results
with open('motion_test_normalized.json', 'r') as f:
    data = json.load(f)

# Extract and normalize text from PDF (same as backend does)
with open('motion.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    original_text = ""
    for page in pdf_reader.pages:
        original_text += page.extract_text()

# Normalize text the same way the backend does
normalized_text = re.sub(r"\s+", " ", original_text)

print("=" * 80)
print("TESTING POSITION ALIGNMENT AFTER FIX")
print("=" * 80)

print(f"\nOriginal text length: {len(original_text)}")
print(f"Normalized text length: {len(normalized_text)}")
print(f"Difference: {len(original_text) - len(normalized_text)} chars removed")

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

print(f"\n{'=' * 80}")
print(f"Found {len(wl_citations)} occurrences of '2024 WL 1232082' in JSON")
print("=" * 80)

# Find actual positions in normalized text
actual_matches = list(re.finditer(r'2024 WL 1232082', normalized_text))
print(f"\nActual positions in normalized text: {len(actual_matches)}")

for i, match in enumerate(actual_matches, 1):
    print(f"\nActual occurrence {i}: Position {match.start()}-{match.end()}")

print(f"\n{'=' * 80}")
print("POSITION ALIGNMENT CHECK")
print("=" * 80)

all_aligned = True
for i, cit in enumerate(wl_citations, 1):
    start = cit['start']
    end = cit['end']
    
    print(f"\nOccurrence {i} from JSON:")
    print(f"  JSON position: {start}-{end}")
    print(f"  Extracted name: {cit['extracted_name']}")
    print(f"  Cluster ID: {cit['cluster_id']}")
    
    if start is not None and end is not None:
        # Check what's at this position in normalized text
        text_at_pos = normalized_text[start:end]
        print(f"  Text at position in normalized text: '{text_at_pos}'")
        
        if '2024 WL 1232082' in text_at_pos:
            print(f"  ✅ POSITION ALIGNED!")
            
            # Show context
            context_start = max(0, start - 100)
            context_end = min(len(normalized_text), end + 100)
            context = normalized_text[context_start:context_end]
            print(f"  Context: ...{context[:50]}[{text_at_pos}]{context[-50:]}...")
            
            # Check if correct case name was extracted
            if 'Doe v. Teachers Council' in cit['extracted_name']:
                print(f"  ✅ CORRECT CASE NAME EXTRACTED")
            elif 'Schiller' in cit['extracted_name']:
                print(f"  ❌ WRONG - Still extracting 'Schiller' (semicolon contamination)")
                all_aligned = False
            else:
                print(f"  ⚠️  Unexpected case name")
        else:
            print(f"  ❌ POSITION MISALIGNED")
            all_aligned = False

print(f"\n{'=' * 80}")
print("SEMICOLON BOUNDARY TEST")
print("=" * 80)

# Find the second occurrence context
if len(actual_matches) >= 2:
    second_pos = actual_matches[1].start()
    context_start = max(0, second_pos - 200)
    context_end = min(len(normalized_text), second_pos + 200)
    context = normalized_text[context_start:context_end]
    
    print(f"\nContext around second occurrence (position {second_pos}):")
    print(f"{context}")
    
    if ';' in context[:200]:
        print(f"\n✅ Semicolon found in context - boundary detection should work")
    else:
        print(f"\n⚠️  No semicolon in context")

print(f"\n{'=' * 80}")
print("CLUSTERING CHECK")
print("=" * 80)

if len(wl_citations) == 2:
    if wl_citations[0]['cluster_id'] == wl_citations[1]['cluster_id']:
        print(f"\n❌ PROBLEM: Both occurrences in same cluster ({wl_citations[0]['cluster_id']})")
        all_aligned = False
    else:
        print(f"\n✅ GOOD: Occurrences in different clusters")
        print(f"  Occurrence 1: Cluster {wl_citations[0]['cluster_id']}")
        print(f"  Occurrence 2: Cluster {wl_citations[1]['cluster_id']}")

print(f"\n{'=' * 80}")
print("FINAL RESULT")
print("=" * 80)

if all_aligned:
    print("\n✅ ✅ ✅ ALL TESTS PASSED! ✅ ✅ ✅")
    print("Position alignment fix is working correctly!")
else:
    print("\n❌ Some issues remain - see details above")
