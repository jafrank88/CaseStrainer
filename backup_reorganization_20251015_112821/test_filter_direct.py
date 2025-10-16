"""
Direct test of contamination filter to verify it's working
"""

from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

# Simulate the exact context from 24-2626.pdf
text = """GOPHER MEDIA LLC v. MELONE Before: Wallace and McAlpin, Circuit Judges, and Berntsen, District Judge. 
The text contains the citation 333 F.3d 1018 referring to Batzel v. Smith."""

document_primary_case_name = "GOPHER MEDIA LLC v. MELONE"

print("=" * 80)
print("DIRECT CONTAMINATION FILTER TEST")
print("=" * 80)
print(f"\nDocument primary case: '{document_primary_case_name}'")
print(f"Text to extract from: '{text[:100]}...'")
print("\nCalling extract_case_name_and_date_unified_master()...")

result = extract_case_name_and_date_unified_master(
    text=text,
    citation="333 F.3d 1018",
    start_index=text.index("333 F.3d 1018"),
    end_index=text.index("333 F.3d 1018") + len("333 F.3d 1018"),
    debug=True,
    document_primary_case_name=document_primary_case_name
)

print("\n" + "=" * 80)
print("RESULT:")
print("=" * 80)
print(f"Case name: '{result.get('case_name', 'N/A')}'")
print(f"Extracted case name: '{result.get('extracted_case_name', 'N/A')}'")
print(f"Year: '{result.get('year', 'N/A')}'")
print(f"Method: '{result.get('method', 'N/A')}'")
print(f"Confidence: {result.get('confidence', 0)}")

# Check if contamination was filtered
case_name = result.get('extracted_case_name', '') or result.get('case_name', '')
is_contaminated = 'gopher' in case_name.lower() or 'melone' in case_name.lower()

print("\n" + "=" * 80)
if is_contaminated:
    print("❌ FAILED: Contamination NOT filtered - still contains document case name")
    print(f"   Extracted: '{case_name}'")
    print(f"   Should NOT contain 'GOPHER' or 'MELONE'")
else:
    print("✅ PASSED: Contamination successfully filtered")
    print(f"   Extracted: '{case_name}'")
print("=" * 80)
