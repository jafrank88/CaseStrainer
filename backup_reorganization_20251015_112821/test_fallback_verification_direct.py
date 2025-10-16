"""
Direct test of fallback verification with known citations
"""

print("="*80)
print("DIRECT FALLBACK VERIFICATION TEST")
print("="*80)

# Test with a mix of citations that will return 404 and some that will verify
test_citations = [
    "347 U.S. 483",      # Brown v. Board - should verify
    "410 U.S. 113",      # Roe v. Wade - should verify  
    "999 U.S. 999",      # Fake - will 404, test fallback
    "123 F.3d 456",      # Generic - likely 404
    "159 Wn.2d 700",     # Bostain - should verify
    "2020 WL 1234567",   # Westlaw - likely 404
]

test_case_names = [
    "Brown v. Board of Education",
    "Roe v. Wade",
    "Fake v. Citation",
    "Smith v. Jones",
    "Bostain v. Food Express",
    "Unknown v. Case",
]

test_dates = ["1954", "1973", "2025", "1997", "2007", "2020"]

print(f"\nTesting {len(test_citations)} citations with verification...")

# Use the unified verification directly
from src.unified_verification_master import get_master_verifier
import asyncio

verifier = get_master_verifier()

print("\n--- Testing Batch Verification ---")

# Run batch verification
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

try:
    results = loop.run_until_complete(
        verifier.verify_citations_batch(
            citations=test_citations,
            extracted_case_names=test_case_names,
            extracted_dates=test_dates
        )
    )
finally:
    loop.close()

print(f"\nResults:")
for i, (cit, result) in enumerate(zip(test_citations, results), 1):
    status = "[OK]" if result.verified else "[NO]"
    source = result.source if result.verified else result.error
    name = result.canonical_name if result.verified else "N/A"
    print(f"{i}. {status} {cit:20} | {source:20} | {name[:40]}")

# Count by source
verified = sum(1 for r in results if r.verified)
sources = {}
for r in results:
    if r.verified:
        sources[r.source] = sources.get(r.source, 0) + 1

print(f"\n--- Summary ---")
print(f"Verified: {verified}/{len(results)} ({verified/len(results)*100:.1f}%)")
print(f"\nSources:")
for source, count in sorted(sources.items()):
    print(f"  {source}: {count}")

# Check if fallback was used
fallback_used = any(r.source == 'fallback' for r in results if r.verified)
print(f"\nFallback verifier used: {'YES' if fallback_used else 'NO'}")

if fallback_used:
    print("\nFallback verified citations:")
    for cit, result in zip(test_citations, results):
        if result.verified and result.source == 'fallback':
            print(f"  - {cit}: {result.canonical_name}")

print("\n" + "="*80)
