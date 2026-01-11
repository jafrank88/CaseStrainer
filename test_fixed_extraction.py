"""
Test the fixed extraction
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING FIXED EXTRACTION")
print("=" * 60)

# Test the problematic text
text = """This presumption of public access does not appear to be rebutted here, though of course Volokh
is handicapped in elaborating on this point by the very facts that Plaintiff's motions are sealed and
that no motion to seal those motions is publicly available. "A motion to seal itself should not
generally require sealing or redaction because litigants should be able to address the applicable
standard without specific reference to confidential information." Allegiant Travel Co. v. Kinzer,
No. 2:21-CV-01649-JAD-NJK, 2022 WL 2819734, at *3 (D. Nev. July 19, 2022)."""

print("Testing citation extraction...")
citations = extract_citations_clean(text)

print("\nResults:")
print("-" * 40)
for cit in citations:
    print(f"Citation: {cit.citation}")
    print(f"Case name: '{cit.extracted_case_name}'")
    print()

print("Expected vs Actual:")
print("-" * 40)
print("2022 WL 2819734 should be: 'Allegiant Travel Co. v. Kinzer'")
if citations:
    print(f"2022 WL 2819734 actually is: '{citations[0].extracted_case_name}'")
    
    if citations[0].extracted_case_name == "Allegiant Travel Co. v. Kinzer":
        print("✅ FIXED!")
    else:
        print("❌ Still broken")
