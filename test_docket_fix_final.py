"""
Test the docket truncation fix
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING DOCKET TRUNCATION FIX")
print("=" * 60)

# Test text with the problematic citation
text = """See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV-
00074-APG-NJK, 2025 WL 1410708, at *1 (D. Nev. Apr. 7, 2025) ("[t]o the extent any confiden-
tial information can be easily redacted" from a "motion to modify stipulated protective order"
"while leaving meaningful information available to the public, the Court must order that redacted
versions be filed rather than sealing entire documents")"""

print("Testing: 2025 WL 1410708")
print("-" * 40)
print("Expected: 'Alexander v. Las Vegas Metro. Police Dep't'")

citations = extract_citations_clean(text)

if citations:
    result = citations[0].extracted_case_name
    print(f"Got:      '{result}'")
    
    if "No. 2:24-CV- 00074-APG-NJK" not in result:
        print("✅ SUCCESS: Docket number properly excluded!")
    else:
        print("❌ FAILED: Docket number still included")
        
    if result == "Alexander v. Las Vegas Metro. Police Dep't":
        print("✅ PERFECT: Exact match!")
    else:
        print(f"⚠️  Close but not exact")
else:
    print("No citations found")
