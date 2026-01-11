"""
Final docket detection patterns
"""

import re

print("FINAL DOCKET DETECTION PATTERNS")
print("=" * 60)

# The actual problematic output
problematic = "Alexander v. Las Vegas Metro. Police Dep't:24-CV- 00074-APG-NJK"
print(f"Problematic case name: '{problematic}'")

# Updated patterns to match the actual format
docket_patterns = [
    r":\d{1,4}[:-]\s*CV-\s*\d{4,}[\w\-]*",  # Matches ":2:24-CV- 00074-APG-NJK"
    r":\d{1,4}[:-]\d{3,4}[\w\-]*",          # General: ":2:24-CV-00074"
    r",\s*No\.\s*[\d\-\w:]+",               # Matches ", No. 2:24-CV-00074"
    r"\bNo\.\s*[\d\-\w:]+",                 # Matches "No. 2:24-CV-00074"
]

def has_docket_number(case_name: str) -> bool:
    """Check if case name contains docket number patterns"""
    for pattern in docket_patterns:
        if re.search(pattern, case_name, re.IGNORECASE):
            print(f"  Matched pattern: {pattern}")
            return True
    return False

def clean_docket_from_case_name(case_name: str) -> str:
    """Remove docket number from case name"""
    cleaned = case_name
    
    # Remove various docket patterns
    for pattern in docket_patterns:
        before = cleaned
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        if before != cleaned:
            print(f"  Applied pattern: {pattern}")
    
    # Clean up any remaining artifacts
    cleaned = re.sub(r"\s*,\s*$", "", cleaned)     # Trailing comma
    cleaned = re.sub(r"\s{2,}", " ", cleaned)      # Multiple spaces
    cleaned = cleaned.strip()
    
    return cleaned

# Test the patterns
print(f"\nTesting docket detection:")
has_docket = has_docket_number(problematic)
print(f"Has docket: {has_docket}")

if has_docket:
    print(f"\nCleaning docket:")
    cleaned = clean_docket_from_case_name(problematic)
    print(f"Cleaned: '{cleaned}'")

# Now let's implement this in the validator
print("\n" + "=" * 60)
print("IMPLEMENTING IN VALIDATOR")
print("-" * 50)

# Add to case_name_validator.py
validator_code = '''
def has_docket_number(case_name: str) -> bool:
    """Check if case name contains docket number patterns"""
    docket_patterns = [
        r":\\d{1,4}[:-]\\s*CV-\\s*\\d{4,}[\\w\\-]*",  # ":2:24-CV- 00074-APG-NJK"
        r":\\d{1,4}[:-]\\d{3,4}[\\w\\-]*",          # General: ":2:24-CV-00074"
        r",\\s*No\\.\\s*[\\d\\-\\w:]+",               # ", No. 2:24-CV-00074"
        r"\\bNo\\.\\s*[\\d\\-\\w:]+",                 # "No. 2:24-CV-00074"
    ]
    return any(re.search(pattern, case_name, re.IGNORECASE) for pattern in docket_patterns)

def clean_docket_from_case_name(case_name: str) -> str:
    """Remove docket number from case name"""
    cleaned = case_name
    docket_patterns = [
        r":\\d{1,4}[:-]\\s*CV-\\s*\\d{4,}[\\w\\-]*",
        r":\\d{1,4}[:-]\\d{3,4}[\\w\\-]*",
        r",\\s*No\\.\\s*[\\d\\-\\w:]+",
        r"\\bNo\\.\\s*[\\d\\-\\w:]+",
    ]
    for pattern in docket_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\\s*,\\s*$", "", cleaned)
    cleaned = re.sub(r"\\s{2,}", " ", cleaned)
    return cleaned.strip()
'''

print("Code to add to case_name_validator.py:")
print(validator_code)

print("\nIntegration plan:")
print("1. Add these functions to case_name_validator.py")
print("2. In is_valid_case_name(), check for docket numbers")
print("3. If docket found, either:")
print("   a. Return False (mark as invalid/unverified)")
print("   b. Clean the docket and validate the cleaned name")
