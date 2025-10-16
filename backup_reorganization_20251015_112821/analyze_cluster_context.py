import PyPDF2
import re

# Open and read PDF
with open('1033940.pdf', 'rb') as pdf_file:
    reader = PyPDF2.PdfReader(pdf_file)
    full_text = ''
    for page in reader.pages:
        full_text += page.extract_text()

# Clean up excessive whitespace
full_text = re.sub(r'\s+', ' ', full_text)

# Find the problematic citations
citations_to_check = [
    '521 U.S. 811',
    '136 S. Ct. 1540',
    '138 L. Ed. 2d 849',
    '117 S. Ct. 2312',
    '194 L. Ed. 2d 635'
]

print("=" * 80)
print("CLUSTER CONTEXT ANALYSIS")
print("=" * 80)

for citation in citations_to_check:
    # Escape dots for regex
    pattern = citation.replace('.', r'\.')
    matches = list(re.finditer(pattern, full_text))
    
    print(f"\n{'='*80}")
    print(f"CITATION: {citation}")
    print(f"Found {len(matches)} occurrence(s)")
    print(f"{'='*80}")
    
    for i, match in enumerate(matches[:3]):  # Show first 3 occurrences
        start = match.start()
        # Get 500 chars before and 200 after
        context_start = max(0, start - 500)
        context_end = min(len(full_text), start + 200)
        context = full_text[context_start:context_end]
        
        # Highlight the citation
        context = context.replace(citation, f"***{citation}***")
        
        print(f"\nOccurrence {i+1} (position {start}):")
        print("-" * 80)
        print(context)
        print("-" * 80)

# Also search for case names that might be near these citations
print(f"\n\n{'='*80}")
print("SEARCHING FOR CASE NAMES NEAR CITATIONS")
print(f"{'='*80}")

case_names = [
    'Spokeo',
    'Raines v. Byrd',
    'Branson',
    'Davis v. Wells Fargo'
]

for case_name in case_names:
    matches = list(re.finditer(re.escape(case_name), full_text, re.IGNORECASE))
    print(f"\n'{case_name}': {len(matches)} occurrence(s)")
    if matches:
        for i, match in enumerate(matches[:2]):
            start = match.start()
            context = full_text[max(0, start-100):min(len(full_text), start+100)]
            print(f"  Position {start}: ...{context}...")
