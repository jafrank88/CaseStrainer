"""
Test the full pipeline to see if the fix works
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

# Force reload
import importlib
import src.utils.strict_context_isolator
importlib.reload(src.utils.strict_context_isolator)
import src.clean_extraction_pipeline
importlib.reload(src.clean_extraction_pipeline)

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING FULL PIPELINE")
print("=" * 60)

# Test text
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
        print("❌ FAILED: Docket number still included")
    else:
        print("✅ SUCCESS: Docket number excluded!")
        
    # Check exact match
    expected = "Alexander v. Las Vegas Metro. Police Dep't"
    if result == expected:
        print(f"✅ PERFECT: Exact match!")
    else:
        print(f"⚠️  Expected: '{expected}'")
        print(f"⚠️  Got:      '{result}'")
else:
    print("No citations found")

print("\n" + "=" * 60)
print("If the docket number is still included, the issue might be:")
print("1. The pattern is not being applied correctly")
print("2. The fallback extraction is being used instead")
print("3. There's caching of old code")
