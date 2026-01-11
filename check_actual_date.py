"""
Check the actual current date and test the F.4th case again
"""

from datetime import datetime
import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("CURRENT DATE CHECK")
print("=" * 60)

# Get actual current date
now = datetime.now()
print(f"Current date: {now.strftime('%Y-%m-%d')}")
print(f"Current year: {now.year}")

print("\n" + "=" * 60)
print("RE-TESTING 146 F.4th 165 (now in 2026)")
print("=" * 60)

# Test the citation again
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
    
    extracted_date = cit.get('extracted_date', 'N/A')
    print(f"\nDate Analysis (in 2026):")
    print(f"  Extracted date from citation: {extracted_date}")
    print(f"  Year in citation text: 2025")
    print(f"  Current year: {now.year}")
    print(f"  This is a PAST case from 2025 (1 year ago)")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("-" * 50)
print("Since it's now 2026:")
print("1. The 146 F.4th 165 case is from 2025 (1 year old)")
print("2. It should be in databases by now")
print("3. If still not found, may be:")
print("   - Citation doesn't exist")
print("   - Database hasn't updated for F.4th series")
print("   - Case number or reporter is incorrect")
print("=" * 60)
