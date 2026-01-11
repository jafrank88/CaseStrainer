"""
Check dates for the F.4th 146 case that wasn't verified
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("CHECKING DATES FOR F.4th 146 CASE")
print("=" * 60)

# Test the specific citation
test_text = "Giuffre v. Maxwell, 146 F.4th 165 (2025)."

print(f"\nTest citation: {test_text}")
print("-" * 50)

from src.citation_extraction_endpoint import extract_citations_production

result = extract_citations_production(test_text)

print(f"\nExtraction Results:")
print(f"  Total citations: {result.get('total', 0)}")

citations = result.get('citations', [])
if citations:
    cit = citations[0]
    print(f"\nCitation details:")
    print(f"  Citation: {str(cit.get('citation', ''))}")
    print(f"  Extracted case name: {cit.get('extracted_case_name', 'N/A')}")
    print(f"  Extracted date: {cit.get('extracted_date', 'N/A')}")
    print(f"  Verified: {cit.get('verified', False)}")
    print(f"  Verification Status: {cit.get('verification_status', 'N/A')}")
    print(f"  Verification Error: {cit.get('verification_error', 'None')}")
    print(f"  Source: {cit.get('source', 'N/A')}")
    
    # Check what year was extracted
    extracted_date = cit.get('extracted_date', 'N/A')
    print(f"\nDate Analysis:")
    print(f"  Extracted date from citation: {extracted_date}")
    print(f"  Year in citation text: 2025")
    print(f"  Current date (when test run): 2025-01-06")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("-" * 50)
print("The citation '146 F.4th 165 (2025)' has:")
print("1. Decision year: 2025 (from citation text)")
print("2. Today's date: 2025-01-06")
print("3. This is a FUTURE case - decided in 2025")
print("4. CourtListener may not have it yet (database lag)")
print("5. Even if in database, dateFiled would be 2025 (recent)")
print("=" * 60)
