#!/usr/bin/env python3

import re

# Test context
context = """Certified questions are questions of law that this court reviews de novo and in light
of the record certified by the federal court. Lopez Demetrio v. Sakuma Bros. Farms, 183
Wn.2d 649, 655, 355 P.3d 258 (2015). Statutory interpretation is also an issue of law we
review de novo. Spokane County v. Dep't of Fish & Wildlife, 192 Wn.2d 453, 457, 430
P.3d 655 (2018)."""

citation = '192 Wn.2d 453'
citation_pos = context.find(citation)
print(f"Citation position: {citation_pos}")

# Test patterns from the extraction code
patterns = [
    r'([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*)\s+v\.\s+([A-Z][a-zA-Z\',\.\&]+(?:\s+[A-Z][a-zA-Z\',\.\&]+)*),\s*(\d+)\s+Wn\.\d+',
    r'([A-Z][^,]+?)\s+v\.\s+([A-Z][^,]+?),\s*(\d+)\s+Wn\.\d+',
]

print("\nChecking all matches and their distances:")
print("=" * 60)

for i, pattern in enumerate(patterns):
    matches = list(re.finditer(pattern, context, re.IGNORECASE))
    print(f"\nPattern {i+1}: {len(matches)} matches")
    
    for j, match in enumerate(matches):
        distance = abs(match.end() - citation_pos)
        match_text = match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
        print(f"  Match {j+1}: distance={distance}, text='{match_text}'")
        
        # Check if this is the Spokane County match
        if 'Spokane County' in match.group(0):
            print(f"    *** THIS IS THE SPOKANE COUNTY MATCH ***")
            print(f"    Volume: {match.group(3) if len(match.groups()) >= 3 else 'N/A'}")
            print(f"    Citation volume: 192")
            print(f"    Volume match: {match.group(3) == '192' if len(match.groups()) >= 3 else 'N/A'}")

print("\n" + "=" * 60)
print("Simulating the extraction logic:")
print("Looking for the closest match within 100 characters...")

best_match = None
min_distance = float('inf')

for i, pattern in enumerate(patterns):
    matches = list(re.finditer(pattern, context, re.IGNORECASE))
    
    for match in matches:
        distance = abs(match.end() - citation_pos)
        
        if distance < 100:  # Within 100 characters
            # Check volume match for patterns 1 and 2
            volume_match = False
            if i < 2 and len(match.groups()) >= 3:
                match_volume = match.group(3)
                citation_volume = "192"
                volume_match = (match_volume == citation_volume)
            
            # Check contamination
            contamination_indicators = ['are', 'ions', 'eview', 'questions', 'we', 'the', 'this', 'also', 'meaning', 'certified', 'review']
            match_text = match.group(0)
            has_contamination = any(match_text.lower().startswith(contam.lower()) for contam in contamination_indicators)
            
            print(f"  Pattern {i+1}, Match: distance={distance}, volume_match={volume_match}, contamination={has_contamination}")
            print(f"    Text: '{match_text[:50]}...'")
            
            if not has_contamination:
                if i < 2 and volume_match:
                    if distance < min_distance:
                        best_match = match
                        min_distance = distance
                        print(f"    *** NEW BEST MATCH (Pattern {i+1}) ***")
                elif i >= 2:  # Patterns 3+ don't require volume match
                    if distance < min_distance:
                        best_match = match
                        min_distance = distance
                        print(f"    *** NEW BEST MATCH (Pattern {i+1}) ***")

if best_match:
    print(f"\n✅ FINAL BEST MATCH:")
    print(f"   Text: '{best_match.group(0)}'")
    print(f"   Distance: {min_distance}")
    print(f"   Plaintiff: '{best_match.group(1)}'")
    print(f"   Defendant: '{best_match.group(2)}'")
else:
    print(f"\n❌ NO MATCH FOUND")



