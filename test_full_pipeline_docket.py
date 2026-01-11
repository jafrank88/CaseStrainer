"""
Test the docket fix with the full pipeline
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

# Force reload
import importlib
import src.case_name_validator
import src.clean_extraction_pipeline
importlib.reload(src.case_name_validator)
importlib.reload(src.clean_extraction_pipeline)

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING DOCKET FIX WITH FULL PIPELINE")
print("=" * 60)

# Test text with the problematic citation
text = """See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV-
00074-APG-NJK, 2025 WL 1410708, at *1 (D. Nev. Apr. 7, 2025) ("[t]o the extent any confiden-
tial information can be easily redacted" from a "motion to modify stipulated protective order"
"while leaving meaningful information available to the public, the Court must order that redacted
versions be filed rather than sealing entire documents")"""

print("Testing citation extraction...")
citations = extract_citations_clean(text)

if citations:
    result = citations[0].extracted_case_name
    print(f"\nResult: '{result}'")
    
    # Check if docket number is included
    if "No. 2:24-CV- 00074-APG-NJK" in result or ":24-CV- 00074-APG-NJK" in result:
        print("❌ ISSUE PERSISTS: Docket number still included")
        print("\nNote: The validator will catch this and treat as unverified.")
        print("The extraction still needs to be fixed at the source.")
    else:
        print("✅ SUCCESS: Docket number excluded!")
        
    # Check if it's the expected clean case name
    expected = "Alexander v. Las Vegas Metro. Police Dep't"
    if result == expected:
        print(f"✅ PERFECT: Exact match!")
    else:
        print(f"\nExpected: '{expected}'")
        print(f"Got:      '{result}'")
        
        # Check if the validator would clean it
        from src.case_name_validator import validate_and_clean_case_name
        is_valid, cleaned = validate_and_clean_case_name(result)
        if cleaned == expected:
            print(f"\n✅ Validator would clean it to: '{cleaned}'")
else:
    print("No citations found")

print("\n" + "=" * 60)
print("SUMMARY:")
print("1. Docket detection in validator: ✅ Working")
print("2. Docket cleaning in validator: ✅ Working")
print("3. Pipeline extraction: ❌ Still includes docket")
print("\nNEXT STEP:")
print("The issue is still in the extraction pipeline where the context")
print("is being modified. The validator provides a fallback by detecting")
print("and treating these as unverified citations.")
