import re
from a_plus_citation_processor import extract_case_name_from_toa_context, extract_year_from_toa_context

# Sample ToA content from the brief
toa_text = """TABLE OF AUTHORITIES
Cases Page(s)
Cathcart v. Andersen, 85 Wn.2d 102 (1975) ......................................................... .32
Chandlerv. Otto, 103 Wn.2d268 (1984) ...................................................... 5, 10-11
Citizens All.for Prop. Rights Legal Fund v. San Juan County, 184 Wn.2d 428, 443, 359 P.3d 753 (2015) ............................................ 33-34
Cougar Business Owners Ass 'n v. State, 97 Wn.2d 466 (1982) 647 P.2d 481 ................... : ................................................................. 50-51
Dore v. Superior Court, 171 Wash. 423, 18 P.2d 51 (1933) ................................. 3, 5"""

# Test each citation
citations = [
    "85 Wn.2d 102",
    "103 Wn.2d268", 
    "184 Wn.2d 428",
    "97 Wn.2d 466",
    "171 Wash. 423"
]

print("=== Testing A+ ToA Extraction ===")
for i, citation in enumerate(citations):
    # Find the citation position in the text
    pos = toa_text.find(citation)
    if pos != -1:
        case_name = extract_case_name_from_toa_context(toa_text, pos)
        year = extract_year_from_toa_context(toa_text, pos + len(citation))
        print(f"{i+1}. Citation: {citation}")
        print(f"   Position: {pos}")
        print(f"   Case Name: '{case_name}'")
        print(f"   Year: '{year}'")
        print()
    else:
        print(f"{i+1}. Citation '{citation}' not found in text")
        print()

# Test the regex patterns directly
print("=== Testing Regex Patterns Directly ===")
patterns = [
    r'([A-Z][A-Za-z0-9&.,\'\s\-]+? v\.? [A-Z][A-Za-z0-9&.,\'\s\-]+?)\s*,',
    r'(In\s+re\s+[A-Za-z0-9&.,\'\s\-]+?)\s*,',
    r'(Dep[\'`]t of [A-Za-z0-9&.,\'\s\-]+? v\. [A-Za-z0-9&.,\'\s\-]+?)\s*,',
]

for i, pattern in enumerate(patterns):
    print(f"Pattern {i+1}: {pattern}")
    matches = list(re.finditer(pattern, toa_text, re.IGNORECASE))
    for match in matches:
        print(f"  Match: '{match.group(1)}' at position {match.start()}")
    print() 