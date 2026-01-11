"""
Test the backup verification method with Giuffre v. Maxwell
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("TESTING BACKUP VERIFICATION METHOD")
print("=" * 60)

print("\nTesting with Giuffre v. Maxwell citation:")
print("-" * 50)
test_text = "Giuffre v. Maxwell, 146 F.4th 165 (2nd Cir. 2025)."

print(f"Citation: {test_text}")

from src.citation_extraction_endpoint import extract_citations_production

result = extract_citations_production(test_text)

print(f"\nResults:")
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
    print(f"  URL: {cit.get('url', 'N/A')}")
    
    # Check if backup search was used
    if cit.get('source') == 'justia_backup_search':
        print(f"\n✅ SUCCESS: Backup verification found the case on Justia!")
        print(f"   Method: {cit.get('verification_method', 'N/A')}")
    elif cit.get('source') == 'courtlistener_backup_search':
        print(f"\n✅ SUCCESS: Backup verification found the case on CourtListener!")
        print(f"   Method: {cit.get('verification_method', 'N/A')}")
    else:
        print(f"\n⚠️  Backup search not used or failed")
        print(f"   Current source: {cit.get('source', 'N/A')}")

print("\n" + "=" * 60)
print("EXPECTED BEHAVIOR:")
print("-" * 50)
print("1. Citation lookup fails (too recent)")
print("2. Backup search triggers")
print("3. Searches Justia for 2nd Circuit 2025 cases")
print("4. Finds Giuffre v. Maxwell")
print("5. Returns verified=True with source='justia_backup_search'")
print("=" * 60)
