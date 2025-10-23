"""
Phase 4 Test: Case Name Extraction Issues

Tests three specific case name extraction problems:
1. "If in Worcester v. Georgia" should be "Martin v. Lessee of Waddell"
2. "State v. Lazcano" should be "Gorman v. City of Woodinville"  
3. "N/A" should be "Outsource Services Management, LLC v. Nooksack Business Corp."
"""

import sys
sys.path.insert(0, '/app')

from src.unified_case_extraction_master import get_master_extractor

# Test Case 1: "If in Worcester" contamination
test1_text = """
If in Worcester v. Georgia, the Court held that the Cherokee Nation 
was a distinct political community in which the laws of Georgia had no force. 
See Martin v. Lessee of Waddell, 16 Pet. 367, 10 L. Ed. 997 (1842).
"""

# Test Case 2: "State v. Lazcano" contamination (nearby case)
test2_text = """
In State v. Lazcano, 136 Wn.2d 188, 960 P.2d 1237 (1998), the court held...
Following this precedent, in Gorman v. City of Woodinville, 175 Wn.2d 68, 
283 P.3d 1082 (2012), the court further clarified...
"""

# Test Case 3: Complex LLC name extraction
test3_text = """
The parties are Outsource Services Management, LLC v. Nooksack Business Corp., 
181 Wn.2d 272, 333 P.3d 380 (2014).
"""

def test_extraction(test_name: str, text: str, citation: str, expected_name: str):
    """Test a single extraction case"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_name}")
    print(f"{'='*80}")
    print(f"Citation: {citation}")
    print(f"Expected: {expected_name}")
    
    extractor = get_master_extractor()
    
    # Find citation position
    start_index = text.find(citation)
    if start_index == -1:
        print(f"❌ SETUP ERROR: Citation '{citation}' not found in text")
        return False
    
    # Extract case name
    result = extractor.extract_case_name_and_date(
        text=text,
        citation=citation,
        start_index=start_index,
        debug=True
    )
    
    extracted_name = result.case_name if result else 'N/A'
    
    print(f"Extracted: {extracted_name}")
    
    # Check result
    if extracted_name == expected_name:
        print(f"✅ PASS")
        return True
    elif 'N/A' in extracted_name or not extracted_name:
        print(f"❌ FAIL: Extraction returned N/A or empty")
        return False
    else:
        print(f"❌ FAIL: Wrong case name extracted")
        return False

# Run all tests
print("\n" + "="*80)
print("PHASE 4 CASE NAME EXTRACTION TESTS")
print("="*80)

results = []

# Test 1: "If in Worcester" contamination
results.append(test_extraction(
    "Issue 1: 'If in Worcester' contamination",
    test1_text,
    "16 Pet. 367",
    "Martin v. Lessee of Waddell"
))

# Test 2: Nearby case contamination
results.append(test_extraction(
    "Issue 2: Nearby 'State v. Lazcano' contamination",
    test2_text,
    "175 Wn.2d 68",
    "Gorman v. City of Woodinville"
))

# Test 3: Complex LLC name
results.append(test_extraction(
    "Issue 3: LLC name extraction failure",
    test3_text,
    "181 Wn.2d 272",
    "Outsource Services Management, LLC v. Nooksack Business Corp."
))

# Summary
print(f"\n{'='*80}")
print(f"SUMMARY: {sum(results)}/{len(results)} tests passed")
print(f"{'='*80}")

if all(results):
    print("✅ ALL TESTS PASSED!")
    sys.exit(0)
else:
    print("❌ SOME TESTS FAILED")
    sys.exit(1)
