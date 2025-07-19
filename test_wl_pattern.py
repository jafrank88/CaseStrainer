import re

# Test text with WL citations
text = "2006 WL 3801910, 2018 WL 2446162, 2019 WL 2516279"
print(f"Test text: '{text}'")

# Test the current pattern
pattern = re.compile(r'\b(\d{4})\s+WL\s+(\d{1,12})\b', re.IGNORECASE)
matches = pattern.findall(text)
print(f"Current pattern matches: {matches}")

# Test without word boundaries
pattern2 = re.compile(r'(\d{4})\s+WL\s+(\d{1,12})', re.IGNORECASE)
matches2 = pattern2.findall(text)
print(f"Without word boundaries: {matches2}")

# Test with finditer to see full matches
for match in pattern2.finditer(text):
    print(f"Full match: '{match.group(0)}' at positions {match.start()}-{match.end()}")
    print(f"  Year: {match.group(1)}, Number: {match.group(2)}") 