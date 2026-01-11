import json
import PyPDF2
import re

# Load the JSON results
with open('motion_test_pointers_fixed.json', 'r') as f:
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
print("FINAL POSITION ALIGNMENT TEST")
print("=" * 80)

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

# Find actual positions in normalized text
actual_matches = list(re.finditer(r'2024 WL 1232082', normalized_text))
print(f"Actual positions in normalized text: {len(actual_matches)}")

for i, match in enumerate(actual_matches, 1):
    print(f"  Actual occurrence {i}: Position {match.start()}-{match.end()}")

print(f"\n{'=' * 80}")
print("CHECKING EACH OCCURRENCE")
print("=" * 80)

success_count = 0
for i, cit in enumerate(wl_citations, 1):
    start = cit['start']
    end = cit['end']
    
    print(f"\nOccurrence {i}:")
    print(f"  JSON position: {start}-{end}")
    print(f"  Extracted name: {cit['extracted_name']}")
    
    if start is not None and end is not None:
        # Check what's at this position in normalized text
        text_at_pos = normalized_text[start:end]
        
        if '2024 WL 1232082' in text_at_pos:
            print(f"  ✅ POSITION ALIGNED!")
            success_count += 1
            
            # Show context
            context_start = max(0, start - 80)
            context_end = min(len(normalized_text), end + 80)
            context = normalized_text[context_start:context_end]
            print(f"  Context: ...{context}...")
            
            # Check case name
            if 'Doe v. Teachers Council' in cit['extracted_name']:
                print(f"  ✅ CORRECT CASE NAME")
            elif 'Schiller' in cit['extracted_name']:
                print(f"  ❌ WRONG CASE NAME (semicolon contamination)")
            else:
                print(f"  ⚠️  Other case name: {cit['extracted_name']}")
        else:
            print(f"  ❌ POSITION MISALIGNED")
            print(f"  Text at position: '{text_at_pos}'")

print(f"\n{'=' * 80}")
print("SUMMARY")
print("=" * 80)

if success_count == len(wl_citations):
    print(f"\n✅ ✅ ✅ SUCCESS! All {success_count} positions are aligned! ✅ ✅ ✅")
else:
    print(f"\n⚠️  {success_count}/{len(wl_citations)} positions aligned")

# Check clustering
if len(wl_citations) >= 2:
    print(f"\nClustering:")
    for i, cit in enumerate(wl_citations, 1):
        print(f"  Occurrence {i}: Cluster {cit['cluster_id']}")
