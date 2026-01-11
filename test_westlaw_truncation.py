"""
Test WestLaw pattern with actual context
"""

import re

print("TESTING WESTLAW PATTERN WITH ACTUAL CONTEXT")
print("=" * 60)

# Test case 1: Allegiant Travel Co. v. Kinzer
text1 = '"A motion to seal itself should not generally require sealing or redaction because litigants should be able to address the applicable standard without specific reference to confidential information." Allegiant Travel Co. v. Kinzer, No. 2:21-CV-01649-JAD-NJK, 2022 WL 2819734, at *3 (D. Nev. July 19, 2022).'

# Test case 2: Doe, Inc. v. Roe
text2 = '"If plaintiff wishes to keep certain information sealed, it . . . must explain why the broad scope of requested sealing is necessary such that the alternative of targeted redactions is insufficient." Doe, Inc. v. Roe, No. MC 21-43 (BAH), 2021 WL 3622166, at *3 (D.D.C. June 3, 2021).'

test_cases = [
    (text1, "2022 WL 2819734", "Allegiant Travel Co. v. Kinzer"),
    (text2, "2021 WL 3622166", "Doe, Inc. v. Roe")
]

for text, citation, expected in test_cases:
    print(f"\nTesting: {citation}")
    print("-" * 40)
    print(f"Expected: {expected}")
    
    # Find citation position
    start_pos = text.find(citation)
    
    # Extract full context as the code does
    full_context = text[max(0, start_pos - 500) : start_pos + 200]
    full_context_clean = re.sub(r"\s+", " ", full_context)
    
    # Apply WestLaw pattern
    wl_pattern = r"([A-Za-z][\w\s&\-\.',]*v\.[\w\s&\-\.',]*?),\s*(?:No\.\s+[^,]+,\s*)?\d{4}\s+WL\s+\d+"
    matches = list(re.finditer(wl_pattern, full_context_clean, re.IGNORECASE))
    
    if matches:
        match = matches[-1]
        result = match.group(1).strip()
        print(f"Got:      {result}")
        
        # Check if it's truncated
        if len(result) < len(expected):
            print(f"⚠️  TRUNCATED: Missing '{expected[len(result):]}'")
    else:
        print("No match found")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("-" * 40)
print("The pattern [A-Za-z][\\w\\s&\\-\\.',]* stops matching at the first")
print("period or special character, causing truncation.")
print("We need a more permissive pattern for multi-word plaintiffs.")
