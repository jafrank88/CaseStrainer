"""
Test the docket pattern fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING DOCKET PATTERN FIX")
print("=" * 60)

# Test text with the problematic citation
text = """explain why the broad scope of requested sealing is necessary such that the alternative of targeted
redactions is insufficient." Doe, Inc. v. Roe, No. MC 21-43 (BAH), 2021 WL 3622166, at *3
(D.D.C. June 3, 2021)."""

print("Testing: 2021 WL 3622166")
print("-" * 40)
print("Expected: 'Doe, Inc. v. Roe'")

citations = extract_citations_clean(text)

if citations:
    result = citations[0].extracted_case_name
    print(f"Got:      '{result}'")
    
    if result == "Doe, Inc. v. Roe":
        print("✅ FIXED!")
    else:
        print("❌ Still broken")
else:
    print("No citations found")
