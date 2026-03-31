"""
Check the actual verification result for this citation
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from unified_verification_master import UnifiedVerificationMaster
import asyncio

async def check_verification():
    master = UnifiedVerificationMaster()
    
    # Test the exact citation
    citation = "684 F.3d 286"
    extracted_case_name = "Union v. N.Y. Transit Auth."
    extracted_date = "2012"
    
    print("=" * 80)
    print("CHECKING VERIFICATION RESULT")
    print("=" * 80)
    print(f"\nCitation: {citation}")
    print(f"Extracted case name: {extracted_case_name}")
    print(f"Extracted date: {extracted_date}")
    
    result = await master.verify_citation(citation, extracted_case_name, extracted_date)
    
    print(f"\nVerification Result:")
    print("-" * 40)
    print(f"Verified: {result.verified}")
    print(f"Canonical name: {result.canonical_name}")
    print(f"Canonical date: {result.canonical_date}")
    print(f"Source: {result.source}")
    print(f"Error: {result.error}")
    
    # Check the raw data for more details
    if hasattr(result, 'raw_data') and result.raw_data:
        print(f"\nRaw Data:")
        print("-" * 40)
        raw = result.raw_data
        print(f"Date filed: {raw.get('date_filed', 'N/A')}")
        print(f"Date created: {raw.get('date_created', 'N/A')}")
        print(f"Date modified: {raw.get('date_modified', 'N/A')}")
        
        # Check if there's amendment info
        if 'date_modified' in raw and raw['date_modified']:
            modified = raw['date_modified'].split('T')[0]
            print(f"\nAmended date: {modified}")
            print("This should be used as the canonical date!")

# Run the check
try:
    asyncio.run(check_verification())
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("RECOMMENDATION:")
print("-" * 40)
print("The verification system should use the most recent")
print("authoritative date (date_modified) as the canonical")
print("date when an opinion has been amended.")
print("=" * 80)
