"""
Deep dive into WestLaw extraction issue
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

print("DEEP DIVE: WESTLAW EXTRACTION ISSUE")
print("=" * 60)

# Test the exact text that's failing
text = """This presumption of public access does not appear to be rebutted here, though of course Volokh
is handicapped in elaborating on this point by the very facts that Plaintiff's motions are sealed and
that no motion to seal those motions is publicly available. "A motion to seal itself should not
generally require sealing or redaction because litigants should be able to address the applicable
standard without specific reference to confidential information." Allegiant Travel Co. v. Kinzer,
No. 2:21-CV-01649-JAD-NJK, 2022 WL 2819734, at *3 (D. Nev. July 19, 2022)."""

citation = "2022 WL 2819734"
start_pos = text.find(citation)

print(f"Citation: {citation}")
print(f"Position: {start_pos}")
print()

# Call the actual extraction function
result = extract_case_name_and_date_unified_master(text, citation, start_pos)

print(f"Extraction result:")
if isinstance(result, dict):
    print(f"  Case name: '{result.get('case_name', 'N/A')}'")
    print(f"  Method: {result.get('method', 'N/A')}")
    print(f"  Confidence: {result.get('confidence', 'N/A')}")
else:
    print(f"  Case name: '{result.case_name}'")
    print(f"  Method: {result.method}")
    print(f"  Confidence: {result.confidence}")

print("\n" + "=" * 60)
print("Expected: 'Allegiant Travel Co. v. Kinzer'")
if isinstance(result, dict):
    print(f"Got:      '{result.get('case_name', 'N/A')}'")
    case_name = result.get('case_name', 'N/A')
else:
    print(f"Got:      '{result.case_name}'")
    case_name = result.case_name

if case_name != "Allegiant Travel Co. v. Kinzer":
    print("\n❌ EXTRACTION IS WRONG")
    print("Let's check what's happening in the special format extraction...")
    
    # Test the special format extraction directly
    from src.unified_case_extraction_master import UnifiedCaseExtractionMaster
    master = UnifiedCaseExtractionMaster()
    
    # Call the special format handler
    special_result = master._extract_special_formats(text, citation, start_pos)
    
    if special_result:
        print(f"\nSpecial format result:")
        print(f"  Case name: '{special_result.case_name}'")
        print(f"  Method: {special_result.method}")
    else:
        print("\nSpecial format extraction returned None")
