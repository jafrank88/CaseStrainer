import re

with open('robert_cassell_doc.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Find the specific citations
patterns = [
    r'8 Wheat\.\s*\d+',
    r'5 L\. Ed\.\s*\d+', 
    r'6 Pet\.\s*\d+',
    r'8 L\. Ed\.\s*\d+',
    r'16 Pet\.\s*\d+',
    r'10 L\. Ed\.\s*\d+',
    r'4 How\.\s*\d+',
    r'11 L\. Ed\.\s*\d+',
]

for pattern in patterns:
    matches = list(re.finditer(pattern, text))
    for match in matches:
        start = max(0, match.start() - 200)
        end = min(len(text), match.end() + 200)
        context = text[start:end]
        print(f"\n{'='*60}")
        print(f"Found: {match.group()}")
        print(f"Position: {match.start()}")
        print(f"Context:\n{context}")
        print(f"{'='*60}\n")
