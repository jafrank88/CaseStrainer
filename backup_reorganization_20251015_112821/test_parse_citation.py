"""Test citation component parsing"""
import re

def _parse_citation_components(citation_text: str):
    """Parse citation into volume, reporter, and page components."""
    if not citation_text:
        return None
    
    # Pattern: volume reporter page
    # CRITICAL FIX: Handle reporters like "F.3d", "F.2d", "P.3d" where the second part starts with a digit
    pattern = r'(\d+)\s+([A-Z][\w\.]+(?:\s+[\w\.]+)*?)\s+(\d+)'
    match = re.search(pattern, citation_text)
    
    if match:
        return {
            'volume': match.group(1),
            'reporter': match.group(2).strip(),
            'page': match.group(3)
        }
    
    return None

# Test with actual false cluster citations
test_citations = [
    "546 U.S. 345",
    "506 U.S. 139",
    "783 F.3d 1328",
    "936 F.3d 240",
    "910 F.3d 1345"
]

print("Testing citation component parsing:\n")
for cit in test_citations:
    result = _parse_citation_components(cit)
    print(f"{cit:20} -> {result}")

# Simulate the validation logic
print("\n" + "=" * 80)
print("Testing validation logic:")
print("=" * 80)

pairs = [
    ("546 U.S. 345", "506 U.S. 139"),
    ("783 F.3d 1328", "936 F.3d 240")
]

for cit1, cit2 in pairs:
    parsed1 = _parse_citation_components(cit1)
    parsed2 = _parse_citation_components(cit2)
    
    print(f"\nComparing: {cit1} vs {cit2}")
    print(f"  Parsed1: {parsed1}")
    print(f"  Parsed2: {parsed2}")
    
    if parsed1 and parsed2:
        vol1, rep1 = parsed1.get('volume'), parsed1.get('reporter')
        vol2, rep2 = parsed2.get('volume'), parsed2.get('reporter')
        
        print(f"  Rep1: '{rep1}', Rep2: '{rep2}'")
        print(f"  Same reporter: {rep1 == rep2}")
        print(f"  Vol1: '{vol1}', Vol2: '{vol2}'")
        print(f"  Different volumes: {vol1 != vol2}")
        
        if rep1 and rep2 and rep1 == rep2 and vol1 != vol2:
            print(f"  ✅ SHOULD BE REJECTED (same reporter, different volumes)")
        else:
            print(f"  ❌ WOULD NOT BE REJECTED")
