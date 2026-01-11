"""
Test citation extraction with proper context
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.clean_extraction_pipeline import extract_citations_clean

print("TESTING INDIVIDUAL CITATIONS")
print("=" * 60)

# Test each citation in isolation first
test_cases = [
    ('"A motion to seal itself should not generally require sealing or redaction because litigants should be able to address the applicable standard without specific reference to confidential information." Allegiant Travel Co. v. Kinzer, No. 2:21-CV-01649-JAD-NJK, 2022 WL 2819734, at *3 (D. Nev. July 19, 2022).', '2022 WL 2819734', 'Allegiant Travel Co. v. Kinzer'),
    ('In re L.A. Times Commc\'ns LLC, 28 F.4th 292, 297 (D.C. Cir. 2022) (criminal case).', '28 F.4th 292', 'In re L.A. Times Commc\'ns LLC'),
]

for text, citation, expected_name in test_cases:
    print(f"\nTesting: {citation}")
    print("-" * 40)
    print(f"Expected: {expected_name}")
    
    citations = extract_citations_clean(text)
    
    if citations:
        cit = citations[0]
        print(f"Got:      '{cit.extracted_case_name}'")
        
        if cit.extracted_case_name == expected_name:
            print("✅ CORRECT")
        else:
            print("❌ WRONG")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("-" * 40)
print("The issue occurs when multiple citations are close together.")
print("The extraction logic is picking up case names from nearby citations.")
