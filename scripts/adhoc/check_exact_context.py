import PyPDF2

with open('motion.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    full_text = ""
    for page in pdf_reader.pages:
        full_text += page.extract_text()

# Position 9721 - 9736 for "2024 WL 1232082"
start = 9721
end = 9736

# Get 500 chars before and after to see full context
context_start = max(0, start - 500)
context_end = min(len(full_text), end + 500)

context = full_text[context_start:context_end]

print("Full context around position 9721-9736:")
print("=" * 80)
print(context)
print("=" * 80)

# Highlight the citation
before = context[:start - context_start]
citation = context[start - context_start:end - context_start]
after = context[end - context_start:]

print("\nBREAKDOWN:")
print(f"BEFORE: ...{before[-200:]}")
print(f"CITATION: [{citation}]")
print(f"AFTER: {after[:200]}...")
