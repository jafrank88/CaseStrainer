#!/usr/bin/env python3

import re
import sys
sys.path.append('src')

# Test the exact context that would be extracted
text = """Certified questions are questions of law that this court reviews de novo and in light
of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430
P.3d 655 (2018)."""

citation = '192 Wn.2d 453'
citation_pos = text.find(citation)

print(f"Citation: '{citation}'")
print(f"Position: {citation_pos}")
print(f"Text length: {len(text)}")

# Simulate the context extraction
context_start = max(0, citation_pos - 500)
context_end = min(len(text), citation_pos + len(citation) + 100)
context = text[context_start:context_end]

print(f"\nContext window ({context_start}:{context_end}):")
print(f"'{context}'")

# Test the patterns from the extraction code
patterns = [
    # Pattern 1: Washington citation format
    r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*),\s*(\d+)\s+Wn\.\d+',
    # Pattern 2: Pacific citation format  
    r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*),\s*(\d+)\s+P\.\d+',
    # Pattern 3: Simplified Washington
    r'([A-Z][^,]+?)\s+v\.\s+([A-Z][^,]+?),\s*(\d+)\s+Wn\.\d+',
    # Pattern 4: Simplified Pacific
    r'([A-Z][^,]+?)\s+v\.\s+([A-Z][^,]+?),\s*(\d+)\s+P\.\d+',
    # Pattern 5: Enhanced Spokane County pattern
    r'([A-Z][a-zA-Z\',\.\&\s]+?)\s+v\.\s+([A-Z][a-zA-Z\',\.\&\s]+?)(?=\s*,\s*\d+|\s+\d+\s+Wn\.\d+|\s+\d+\s+P\.\d+|$)',
]

print(f"\nTesting patterns against context:")
print("=" * 60)

for i, pattern in enumerate(patterns, 1):
    print(f"\nPattern {i}: {pattern}")
    matches = list(re.finditer(pattern, context, re.IGNORECASE))
    print(f"Found {len(matches)} matches:")
    
    for j, match in enumerate(matches):
        print(f"  Match {j+1}:")
        print(f"    Full: '{match.group(0)}'")
        if len(match.groups()) >= 1:
            print(f"    Group 1 (plaintiff): '{match.group(1)}'")
        if len(match.groups()) >= 2:
            print(f"    Group 2 (defendant): '{match.group(2)}'")
        if len(match.groups()) >= 3:
            print(f"    Group 3 (volume): '{match.group(3)}'")
        print(f"    Position: {match.start()}-{match.end()}")
        
        # Check if this is the problematic match
        if len(match.groups()) >= 2 and match.group(2) == 'Dep':
            print(f"    *** THIS IS THE PROBLEMATIC MATCH! ***")
            print(f"    The defendant is truncated to '{match.group(2)}'")
            print(f"    Full match text: '{match.group(0)}'")
            
            # Let's see what comes after "Dep" in the context
            match_end = match.end()
            after_match = context[match_end:match_end+50]
            print(f"    Text after match: '{after_match}'")

print(f"\n" + "=" * 60)
print("Looking for the specific Spokane County case:")
spokane_pattern = r'(Spokane County)\s+v\.\s+(Dep\'t of Fish & Wildlife)'
spokane_match = re.search(spokane_pattern, context, re.IGNORECASE)
if spokane_match:
    print(f"✅ FOUND: '{spokane_match.group(0)}'")
    print(f"   Plaintiff: '{spokane_match.group(1)}'")
    print(f"   Defendant: '{spokane_match.group(2)}'")
else:
    print("❌ NOT FOUND")
    
    # Let's try a more flexible pattern
    flexible_pattern = r'(Spokane County)\s+v\.\s+(Dep[^,]*?)(?=\s*,\s*\d+|\s+\d+\s+Wn\.\d+|\s+\d+\s+P\.\d+|$)'
    flexible_match = re.search(flexible_pattern, context, re.IGNORECASE)
    if flexible_match:
        print(f"✅ FOUND with flexible pattern: '{flexible_match.group(0)}'")
        print(f"   Plaintiff: '{flexible_match.group(1)}'")
        print(f"   Defendant: '{flexible_match.group(2)}'")
    else:
        print("❌ NOT FOUND with flexible pattern either")
