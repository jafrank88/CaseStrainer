import re

# Simulate the text context
text = """Doe v. Columbia Univ., No. 23 CIV. 10393 (DEH), 2024 WL 4149252, at *6 (S.D.N.Y. Sept. 11, 2024) ("the Court GRANTS Volokh's motion to intervene in Columbia and Kachalia"); Mastriano v. Gregory, No. CIV-24-567-F, 2024 WL 4003343, at *5 (W.D. Okla. Aug. 26, 2024) ("The Motion of Prof. Eugene Volokh to Intervene to Unseal Record Documents . . . is GRANTED.")"""

# Find the position of "2024 WL 4003343"
citation = "2024 WL 4003343"
start_index = text.find(citation)
print(f"Citation '{citation}' found at position: {start_index}")

# Extract context as the code does
context_before = text[max(0, start_index - 500) : start_index]
full_context = text[max(0, start_index - 500) : min(len(text), start_index + 200)]

# Normalize whitespace
context_clean = re.sub(r"\s+", " ", context_before)
full_context_clean = re.sub(r"\s+", " ", full_context)

print(f"\n=== BEFORE SEMICOLON DETECTION ===")
print(f"context_clean length: {len(context_clean)}")
print(f"context_clean: '{context_clean}'")
print(f"\nfull_context_clean length: {len(full_context_clean)}")
print(f"full_context_clean: '{full_context_clean}'")

# Apply semicolon boundary detection to context_clean
if ";" in context_clean:
    last_semicolon_pos = context_clean.rfind(";")
    print(f"\n=== SEMICOLON IN context_clean ===")
    print(f"Semicolon found at position: {last_semicolon_pos}")
    old_context = context_clean
    context_clean = context_clean[last_semicolon_pos + 1:].strip()
    print(f"Old context (last 100): '{old_context[-100:]}'")
    print(f"New context: '{context_clean}'")

# Apply semicolon boundary detection to full_context_clean
if ";" in full_context_clean:
    last_semicolon_pos = full_context_clean.rfind(";")
    print(f"\n=== SEMICOLON IN full_context_clean ===")
    print(f"Semicolon found at position: {last_semicolon_pos}")
    old_full_context = full_context_clean
    full_context_clean = full_context_clean[last_semicolon_pos + 1:].strip()
    print(f"Old full_context (last 100): '{old_full_context[-100:]}'")
    print(f"New full_context (first 100): '{full_context_clean[:100]}'")
    print(f"New full_context (full): '{full_context_clean}'")

# Test the WL docket pattern
print(f"\n=== TESTING WL DOCKET PATTERN ===")
wl_pattern = r"([A-Za-z][\w\s&\-\.',]*v\.[\w\s&\-\.',]*?),\s*(?:No\.\s+[^,]+,\s*)?\d{4}\s+WL\s+\d+"
matches = list(re.finditer(wl_pattern, full_context_clean, re.IGNORECASE))
print(f"Number of matches: {len(matches)}")
for i, match in enumerate(matches):
    print(f"Match {i+1}: '{match.group(0)}'")
    print(f"  Case name (group 1): '{match.group(1)}'")
