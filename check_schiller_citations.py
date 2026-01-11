import json

with open('motion_test_results_final.json', 'r') as f:
    data = json.load(f)

print("Checking Schiller citations...")
print("=" * 80)

# Find Schiller citations
schiller_citations = []
for cit in data.get('citations', []):
    citation_text = cit.get('citation', '')
    if '2024 WL 1232082' in citation_text or '2006 WL 2788256' in citation_text:
        schiller_citations.append({
            'citation': citation_text,
            'start_index': cit.get('start_index'),
            'end_index': cit.get('end_index'),
            'extracted_case_name': cit.get('extracted_case_name'),
            'extracted_date': cit.get('extracted_date'),
            'cluster_id': cit.get('cluster_id'),
            'context': cit.get('context', '')[:200]
        })

for cit in schiller_citations:
    print(f"\nCitation: {cit['citation']}")
    print(f"  Position: {cit['start_index']} - {cit['end_index']}")
    print(f"  Extracted name: {cit['extracted_case_name']}")
    print(f"  Extracted date: {cit['extracted_date']}")
    print(f"  Cluster ID: {cit['cluster_id']}")
    print(f"  Context: {cit['context'][:150]}...")

# Now extract the text from motion.pdf to see the actual context
print("\n" + "=" * 80)
print("Extracting text from motion.pdf to see actual context...")
print("=" * 80)

import PyPDF2

with open('motion.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    full_text = ""
    for page in pdf_reader.pages:
        full_text += page.extract_text()

# Find the citations in the text
for cit in schiller_citations:
    start = cit['start_index']
    end = cit['end_index']
    
    # Get surrounding context (200 chars before and after)
    context_start = max(0, start - 200)
    context_end = min(len(full_text), end + 200)
    
    context = full_text[context_start:context_end]
    
    print(f"\n\nCitation: {cit['citation']}")
    print(f"Position: {start} - {end}")
    print(f"\nContext (200 chars before and after):")
    print("-" * 80)
    print(context)
    print("-" * 80)
