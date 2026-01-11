"""
Debug year extraction to understand why Biden v. Nebraska shows 2001 instead of 2023.
"""
import logging
from src.unified_case_extraction_master import extract_case_name_and_date_unified_master

logging.basicConfig(level=logging.DEBUG, format='%(message)s')

# Test cases from the user's results showing wrong years
test_cases = [
    {
        "citation": "600 U.S. 477",
        "expected_name": "Biden v. Nebraska",
        "expected_year": "2023",
        "wrong_year": "2001",
        # Simulated context - we need to see what the actual document context looks like
        "context": """
        Biden v. Nebraska, 600 U.S. 477 (2023), the Supreme Court held...
        This case was decided in 2023, not 2001.
        """
    },
    {
        "citation": "125 U.S. 136",
        "expected_name": "Tilghman v. Proctor",
        "expected_year": "1888",
        "wrong_year": "2025",
        "context": """
        Tilghman v. Proctor, 125 U.S. 136 (1888), established...
        This 1888 case is still cited in 2025.
        """
    },
]

print("="*80)
print("YEAR EXTRACTION DEBUG TEST")
print("="*80)

for test in test_cases:
    print(f"\n{'─'*80}")
    print(f"Citation: {test['citation']}")
    print(f"Expected: {test['expected_name']} ({test['expected_year']})")
    print(f"Wrong year shown: {test['wrong_year']}")
    print(f"{'─'*80}")
    
    # Extract using the unified master
    result = extract_case_name_and_date_unified_master(
        text=test['context'],
        citation=test['citation'],
        start_index=test['context'].find(test['citation']),
        debug=True
    )
    
    print(f"\n📊 EXTRACTION RESULT:")
    print(f"   Case Name: {result.get('extracted_case_name', 'N/A')}")
    print(f"   Year: {result.get('extracted_year', 'N/A')}")
    print(f"   Method: {result.get('method', 'N/A')}")
    print(f"   Confidence: {result.get('confidence', 'N/A')}")
    
    # Check if it matches expected
    extracted_year = result.get('extracted_year', 'N/A')
    if extracted_year == test['expected_year']:
        print(f"   ✅ CORRECT YEAR")
    elif extracted_year == test['wrong_year']:
        print(f"   ❌ WRONG YEAR (got {extracted_year}, expected {test['expected_year']})")
    else:
        print(f"   ⚠️  UNEXPECTED YEAR (got {extracted_year}, expected {test['expected_year']}, wrong was {test['wrong_year']})")

print("\n" + "="*80)
print("NOTE: This test uses simulated context. The real issue is likely in the")
print("actual PDF text where years appear in unexpected positions.")
print("="*80)
