"""
Refined docket detection and cleaning
"""

import re

print("REFINED DOCKET DETECTION AND CLEANING")
print("=" * 60)

# The actual problematic output
problematic = "Alexander v. Las Vegas Metro. Police Dep't:24-CV- 00074-APG-NJK"
print(f"Problematic case name: '{problematic}'")

# Better docket patterns
docket_patterns = [
    r":\d{1,4}[:-]\d{3,4}[\w\-]*",  # Matches ":2:24-CV-00074-APG-NJK"
    r",\s*No\.\s*[\d\-\w:]+",       # Matches ", No. 2:24-CV-00074-APG-NJK"
    r"\bNo\.\s*[\d\-\w:]+",         # Matches "No. 2:24-CV-00074-APG-NJK"
    r"\b\d{1,4}[:-]\d{3,4}[\w\-]*", # Matches "2:24-CV-00074-APG-NJK"
]

def has_docket_number(case_name: str) -> bool:
    """Check if case name contains docket number patterns"""
    for pattern in docket_patterns:
        if re.search(pattern, case_name):
            return True
    return False

def clean_docket_from_case_name(case_name: str) -> str:
    """Remove docket number from case name"""
    cleaned = case_name
    
    # Remove various docket patterns
    for pattern in docket_patterns:
        cleaned = re.sub(pattern, "", cleaned)
    
    # Clean up any remaining artifacts
    cleaned = re.sub(r"\s*,\s*$", "", cleaned)     # Trailing comma
    cleaned = re.sub(r"\s{2,}", " ", cleaned)      # Multiple spaces
    cleaned = cleaned.strip()
    
    return cleaned

# Test the refined patterns
print(f"\nHas docket: {has_docket_number(problematic)}")
cleaned = clean_docket_from_case_name(problematic)
print(f"Cleaned: '{cleaned}'")

# Test with other examples
test_cases = [
    "Doe v. Roe, No. 123",
    "Smith v. Jones:2023-CV-456",
    "Brown v. Board, No. 5:2024-APG-789",
    "Normal Case Name v. Defendant",
]

print("\n" + "-" * 50)
print("Testing with various cases:")
for case in test_cases:
    has_docket = has_docket_number(case)
    cleaned = clean_docket_from_case_name(case)
    print(f"'{case}'")
    print(f"  Has docket: {has_docket}")
    print(f"  Cleaned: '{cleaned}'")

print("\n" + "=" * 60)
print("IMPLEMENTATION PLAN:")
print("1. Add docket detection to case_name_validator.py")
print("2. When docket is detected, mark as unverified")
print("3. Apply cleaning in the extraction pipeline")
print("4. This treats docket-contaminated names as unverified citations")
