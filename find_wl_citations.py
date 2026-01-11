import PyPDF2
import re

with open('motion.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    full_text = ""
    for page in pdf_reader.pages:
        full_text += page.extract_text()

# Find all occurrences of "2024 WL 1232082"
pattern = r'2024 WL 1232082'
matches = list(re.finditer(pattern, full_text))

print(f"Found {len(matches)} occurrences of '2024 WL 1232082':")
print("=" * 80)

for i, match in enumerate(matches, 1):
    start = match.start()
    end = match.end()
    
    # Get context (300 chars before and after)
    context_start = max(0, start - 300)
    context_end = min(len(full_text), end + 300)
    
    context = full_text[context_start:context_end]
    
    print(f"\nOccurrence {i}:")
    print(f"Position: {start} - {end}")
    print(f"Context:")
    print("-" * 80)
    # Highlight the citation
    before = context[:start - context_start]
    citation = context[start - context_start:end - context_start]
    after = context[end - context_start:]
    print(f"{before}[[[{citation}]]]{after}")
    print("-" * 80)

# Also find "2006 WL 2788256"
print("\n\n" + "=" * 80)
pattern2 = r'2006 WL 2788256'
matches2 = list(re.finditer(pattern2, full_text))

print(f"Found {len(matches2)} occurrences of '2006 WL 2788256':")
print("=" * 80)

for i, match in enumerate(matches2, 1):
    start = match.start()
    end = match.end()
    
    # Get context (300 chars before and after)
    context_start = max(0, start - 300)
    context_end = min(len(full_text), end + 300)
    
    context = full_text[context_start:context_end]
    
    print(f"\nOccurrence {i}:")
    print(f"Position: {start} - {end}")
    print(f"Context:")
    print("-" * 80)
    # Highlight the citation
    before = context[:start - context_start]
    citation = context[start - context_start:end - context_start]
    after = context[end - context_start:]
    print(f"{before}[[[{citation}]]]{after}")
    print("-" * 80)
