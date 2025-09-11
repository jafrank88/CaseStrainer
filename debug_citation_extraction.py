import re

# Test the citation extraction from blocks
citations_text = '169 Wn.2d 815, 820, 239 P.3d 354'
parts = [part.strip() for part in citations_text.split(',')]
print('Parts:', parts)

# Test the patterns from citation_extractor.py
patterns = [
    re.compile(r'\b\d+\s+Wn\.\s*2d\s*\n?\s*\d+\b'),
    re.compile(r'\b\d+\s+P\.(?:\s*\d*d?\s+\d+\b|\s*\d+\.\d+\b)')
]

for part in parts:
    print(f'Part: "{part}"')
    matched = False
    for pattern in patterns:
        if pattern.search(part):
            print(f'  Matches pattern: {pattern.pattern}')
            matched = True
            break
    if not matched:
        print(f'  No pattern match')
