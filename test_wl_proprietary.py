"""
Test why WL citations are not showing "proprietary format" message
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from unified_verification_master import UnifiedVerificationMaster
import asyncio

async def test_wl_citations():
    master = UnifiedVerificationMaster()
    
    # Test WL citations from the user's example
    wl_citations = [
        ("2022 WL 15153410", "Doe v. City of New York", "2022"),
        ("2024 WL 4149252", "Doe v. Columbia Univ.", "2024"),
        ("2024 WL 4003343", "Mastriano v. Gregory", "2024"),
        ("2024 WL 1232082", "Doe v. Teachers Council, Inc.", "2024"),
        ("2022 WL 2819734", "Travel Co. v. Kinzer", "2022"),
        ("2025 WL 1410708", "Alexander v. Las Vegas Metro. Police Dep't", "2025"),
        ("2006 WL 2788256", "Schiller v. City of New York", "2006"),
        ("2021 WL 3622166", "Doe, Inc. v. Roe", "2021"),
    ]
    
    print("=" * 80)
    print("TESTING WL CITATIONS")
    print("=" * 80)
    
    for citation, case_name, date in wl_citations:
        print(f"\n{'-' * 60}")
        print(f"Citation: {citation}")
        print(f"Case: {case_name}")
        print(f"Date: {date}")
        
        result = await master.verify_citation(citation, case_name, date)
        
        print(f"\nResult:")
        print(f"  Verified: {result.verified}")
        print(f"  Source: {result.source}")
        print(f"  Error: {result.error}")
        
        # Check if it's a WL citation that should have proprietary message
        if "WL" in citation and not result.verified:
            if "proprietary" not in str(result.error).lower():
                print(f"\n⚠️  WARNING: WL citation not marked as proprietary!")
                print(f"   Expected: 'proprietary format' message")
                print(f"   Actual: '{result.error}'")

# Run the test
try:
    asyncio.run(test_wl_citations())
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("ANALYSIS:")
print("-" * 40)
print("WL citations are Westlaw's proprietary format.")
print("They should be marked as unverified with aproprietary format message.")
print("If they're not, the verification system may be:")
print("1. Trying to verify them through other sources")
print("2. Not detecting them as WL citations properly")
print("3. Missing the proprietary format check")
print("=" * 80)
