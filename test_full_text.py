"""
Test the full text with all citations
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING FULL TEXT WITH ALL CITATIONS")
print("=" * 60)

# The full text with multiple citations
text = """This presumption of public access does not appear to be rebutted here, though of course Volokh
is handicapped in elaborating on this point by the very facts that Plaintiff's motions are sealed and
that no motion to seal those motions is publicly available. "A motion to seal itself should not
generally require sealing or redaction because litigants should be able to address the applicable
standard without specific reference to confidential information." Allegiant Travel Co. v. Kinzer,
No. 2:21-CV-01649-JAD-NJK, 2022 WL 2819734, at *3 (D. Nev. July 19, 2022).
And even if there are some items in Plaintiff's motions that need to be kept confidential, the
common-law right of access requires that a district court consider "whether redaction would be an
appropriate alternative" to full sealing. In re L.A. Times Commc'ns LLC, 28 F.4th 292, 297 (D.C.
Cir. 2022) (criminal case). "If plaintiff wishes to keep certain information sealed, it . . . must ex-
plain why the broad scope of requested sealing is necessary such that the alternative of targeted
redactions is insufficient." Doe, Inc. v. Roe, No. MC 21-43 (BAH), 2021 WL 3622166, at *3
(D.D.C. June 3, 2021). See also, e.g., Alexander v. Las Vegas Metro. Police Dep't, No. 2:24-CV-
00074-APG-NJK, 2025 WL 1410708, at *1 (D. Nev. Apr. 7, 2025)"""

print("Extracting citations...")
citations = extract_citations_clean(text)

print("\nResults:")
print("-" * 40)
expected = [
    ("2022 WL 2819734", "Allegiant Travel Co. v. Kinzer"),
    ("28 F.4th 292", "In re L.A. Times Commc'ns LLC"),
    ("2021 WL 3622166", "Doe, Inc. v. Roe"),
    ("2025 WL 1410708", "Alexander v. Las Vegas Metro. Police Dep't")
]

all_correct = True
for i, cit in enumerate(citations):
    expected_citation, expected_name = expected[i]
    print(f"{i+1}. {cit.citation}")
    print(f"   Expected: '{expected_name}'")
    print(f"   Got:      '{cit.extracted_case_name}'")
    
    if cit.extracted_case_name == expected_name:
        print("   ✓ CORRECT")
    else:
        print("   ✗ WRONG")
        all_correct = False
    print()

print("=" * 60)
if all_correct:
    print("SUCCESS: All citations extracted correctly!")
else:
    print("Some citations are still incorrect.")
