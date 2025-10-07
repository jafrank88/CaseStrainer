"""
Test case name extraction for the Raines v. Byrd bug
"""
import sys
sys.path.insert(0, 'src')

from unified_case_extraction_master import extract_case_name_and_date_unified_master

# Test case from the actual PDF
test_text = """
must be protected by the provision of a statute in order to have standing to 
sue to enforce it. Raines v. Byrd, 521 U.S. 811, 820 n.3, 117 S. Ct. 2312, 
138 L. Ed. 2d 849 (1997)
"""

# Find the citation position
citation = "521 U.S. 811"
start_index = test_text.find(citation)
end_index = start_index + len(citation)

print("=" * 80)
print("TESTING RAINES V. BYRD EXTRACTION")
print("=" * 80)
print(f"\nTest Text:\n{test_text}")
print(f"\nCitation: {citation}")
print(f"Position: {start_index}-{end_index}")
print(f"\nContext before citation (100 chars):")
print(f"'{test_text[max(0, start_index-100):start_index]}'")
print("\n" + "=" * 80)

# Test extraction
result = extract_case_name_and_date_unified_master(
    text=test_text,
    citation=citation,
    start_index=start_index,
    end_index=end_index,
    debug=True
)

print("\nEXTRACTION RESULT:")
print("=" * 80)
print(f"Case Name: {result.get('case_name')}")
print(f"Year: {result.get('year')}")
print(f"Confidence: {result.get('confidence')}")
print(f"Method: {result.get('method')}")
print(f"Debug Info: {result.get('debug_info')}")

print("\n" + "=" * 80)
if result.get('case_name') == "Raines v. Byrd":
    print("✅ TEST PASSED: Correctly extracted 'Raines v. Byrd'")
else:
    print(f"❌ TEST FAILED: Expected 'Raines v. Byrd', got '{result.get('case_name')}'")
print("=" * 80)

# Test the Spokeo case too
print("\n\n" + "=" * 80)
print("TESTING SPOKEO EXTRACTION")
print("=" * 80)

test_text2 = """
Congress cannot erase Article III's standing requirements by statutorily 
granting the right to sue to a plaintiff who would not otherwise have standing.' 
Spokeo, Inc. v. Robins, 578 U.S. 330, 336, 136 S. Ct. 1540, 194 L. Ed. 2d 635 (2016)
"""

citation2 = "136 S. Ct. 1540"
start_index2 = test_text2.find(citation2)
end_index2 = start_index2 + len(citation2)

print(f"\nTest Text:\n{test_text2}")
print(f"\nCitation: {citation2}")
print(f"Position: {start_index2}-{end_index2}")

result2 = extract_case_name_and_date_unified_master(
    text=test_text2,
    citation=citation2,
    start_index=start_index2,
    end_index=end_index2,
    debug=True
)

print("\nEXTRACTION RESULT:")
print("=" * 80)
print(f"Case Name: {result2.get('case_name')}")
print(f"Year: {result2.get('year')}")
print(f"Confidence: {result2.get('confidence')}")
print(f"Method: {result2.get('method')}")

print("\n" + "=" * 80)
if result2.get('case_name') == "Spokeo, Inc. v. Robins":
    print("✅ TEST PASSED: Correctly extracted 'Spokeo, Inc. v. Robins'")
else:
    print(f"❌ TEST FAILED: Expected 'Spokeo, Inc. v. Robins', got '{result2.get('case_name')}'")
print("=" * 80)
