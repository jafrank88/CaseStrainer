"""
Deep investigation of docket number truncation
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')
import re

print("DEEP INVESTIGATION OF DOCKET TRUNCATION")
print("=" * 60)

# The transformation we're seeing:
# Input:  'See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,'
# Output: 'Alexander v. Las Vegas Metro. Police Dep't:24-CV- 00074-APG-NJK'

print("\n1. CHECKING FOR PATTERNS THAT MODIFY ', No.' TO ':'")
print("-" * 50)

# Look for patterns that might be doing this transformation
test_context = "Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV- 00074-APG-NJK,"

# Common patterns that might cause this
patterns_to_check = [
    # Pattern that extracts docket and leaves colon
    (r",\s*No\.\s+(\d+:)", "Captures just the number part after No."),
    (r",\s*No\.\s+([^,]+)", "Captures entire docket"),
    (r",\s*No\.\s+2:24", "Specific to our case"),
    (r",\s*No\.\s*(\d:)", "Captures number starting with digit and colon"),
]

for pattern, desc in patterns_to_check:
    match = re.search(pattern, test_context)
    if match:
        print(f"Found: {desc}")
        print(f"  Pattern: {pattern}")
        print(f"  Match: '{match.group()}'")

print("\n2. CHECKING CLEAN-EXTRACTION-PIPELINE FOR MODIFICATIONS")
print("-" * 50)

# Let me check if there's something in the clean_extraction_pipeline
# that modifies the context before passing to strict_context_isolator

print("Looking for patterns in clean_extraction_pipeline.py...")

# Check if there's a pattern that modifies docket numbers
docket_patterns = [
    r"docket.*clean",
    r"No\..*sub",
    r",\s*No\.",
    r"clean.*No\.",
]

print("\nSearching for docket-related patterns...")

print("\n3. HYPOTHESIS: CONTEXT MODIFICATION IN ADAPTIVE CONTEXT")
print("-" * 50)

print("The issue might be in get_adaptive_context_for_citation")
print("or in how the context is being processed before pattern matching.")

print("\n4. ALTERNATIVE APPROACH: TREAT AS UNVERIFIED CITATION")
print("-" * 50)

print("If the docket number is causing issues, we could:")
print("1. Detect when a case name contains docket-like patterns")
print("2. Mark it as unverified")
print("3. Return a cleaner version without the docket")

# Let's implement this approach
def has_docket_number(case_name: str) -> bool:
    """Check if case name contains docket number patterns"""
    docket_patterns = [
        r",\s*No\.\s*[\d\-\w:]+",
        r":\d{1,4}[:-]\d{3,4}",  # Matches ":2:24-CV" or similar
        r"CV-\d{4,}",  # Matches "CV-00074"
        r"APG-\d+",    # Matches "APG-NJK"
    ]
    return any(re.search(pattern, case_name) for pattern in docket_patterns)

def clean_docket_from_case_name(case_name: str) -> str:
    """Remove docket number from case name"""
    # Remove ", No. ..." patterns
    cleaned = re.sub(r",\s*No\.\s*[\d\-\w:]+", "", case_name)
    # Remove any remaining docket-like patterns
    cleaned = re.sub(r":\d{1,4}[:-]\d{3,4}[\w\-]*", "", cleaned)
    cleaned = re.sub(r"CV-\d{4,}[\w\-]*", "", cleaned)
    cleaned = re.sub(r"APG-\d+[\w\-]*", "", cleaned)
    # Clean up trailing punctuation
    cleaned = re.sub(r"\s*,\s*$", "", cleaned)
    return cleaned.strip()

# Test this approach
test_case = "Alexander v. Las Vegas Metro. Police Dep't:24-CV- 00074-APG-NJK"
print(f"\nTesting with: '{test_case}'")
print(f"Has docket: {has_docket_number(test_case)}")
print(f"Cleaned: '{clean_docket_from_case_name(test_case)}'")

print("\n" + "=" * 60)
print("RECOMMENDATION:")
print("Add docket number detection and cleaning in the validation step")
print("or after extraction to handle cases where docket numbers are included.")
