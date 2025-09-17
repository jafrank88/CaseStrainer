#!/usr/bin/env python3

import re

# Test the fallback patterns
text = """Certified questions are questions of law that this court reviews de novo and in light
of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430
P.3d 655 (2018)."""

citation = '192 Wn.2d 453'
citation_pos = text.find(citation)

# Simulate the fallback pattern search
search_radius = 200
search_start = max(0, citation_pos - search_radius)
search_end = min(len(text), citation_pos + len(citation) + search_radius)
search_text = text[search_start:search_end]

print(f"Citation: '{citation}'")
print(f"Position: {citation_pos}")
print(f"Search text ({search_start}:{search_end}):")
print(f"'{search_text}'")

# Test the fallback patterns
fallback_patterns = [
    r'([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*(?:LLC|Inc\.?|Corp\.?|Ltd\.?|Co\.?))',
    r'([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]*(?:\s+[A-Z][a-zA-Z\',\.\&]*)*)',
]

print(f"\nTesting fallback patterns:")
print("=" * 60)

for i, pattern in enumerate(fallback_patterns, 1):
    print(f"\nFallback Pattern {i}: {pattern}")
    matches = list(re.finditer(pattern, search_text, re.IGNORECASE))
    print(f"Found {len(matches)} matches:")
    
    for j, match in enumerate(matches):
        print(f"  Match {j+1}:")
        print(f"    Full: '{match.group(0)}'")
        if len(match.groups()) >= 1:
            print(f"    Group 1 (plaintiff): '{match.group(1)}'")
        if len(match.groups()) >= 2:
            print(f"    Group 2 (defendant): '{match.group(2)}'")
        print(f"    Position: {match.start()}-{match.end()}")
        
        # Check if this is the problematic match
        if len(match.groups()) >= 2 and match.group(2) == 'Dep':
            print(f"    *** THIS IS THE PROBLEMATIC MATCH! ***")
            print(f"    The defendant is truncated to '{match.group(2)}'")
            print(f"    Full match text: '{match.group(0)}'")
            
            # Let's see what comes after "Dep" in the search text
            match_end = match.end()
            after_match = search_text[match_end:match_end+50]
            print(f"    Text after match: '{after_match}'")

print(f"\n" + "=" * 60)
print("Looking for the specific Spokane County case in search text:")
spokane_pattern = r'(Spokane County)\s+v\.\s+(Dep\'t of Fish & Wildlife)'
spokane_match = re.search(spokane_pattern, search_text, re.IGNORECASE)
if spokane_match:
    print(f"✅ FOUND: '{spokane_match.group(0)}'")
    print(f"   Plaintiff: '{spokane_match.group(1)}'")
    print(f"   Defendant: '{spokane_match.group(2)}'")
else:
    print("❌ NOT FOUND")
    
    # Let's try a more flexible pattern
    flexible_pattern = r'(Spokane County)\s+v\.\s+(Dep[^,]*?)(?=\s*,\s*\d+|\s+\d+\s+Wn\.\d+|\s+\d+\s+P\.\d+|$)'
    flexible_match = re.search(flexible_pattern, search_text, re.IGNORECASE)
    if flexible_match:
        print(f"✅ FOUND with flexible pattern: '{flexible_match.group(0)}'")
        print(f"   Plaintiff: '{flexible_match.group(1)}'")
        print(f"   Defendant: '{flexible_match.group(2)}'")
    else:
        print("❌ NOT FOUND with flexible pattern either")



