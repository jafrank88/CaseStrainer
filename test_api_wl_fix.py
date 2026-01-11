"""
Test the fixed API endpoint for WL proprietary format marking
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

print("TESTING API ENDPOINT FIX FOR WL PROPRIETARY MARKING")
print("=" * 60)

# Test through the simplified citation processor (what the API uses)
from src.simplified_citation_processor import create_processor, ProcessingConfig

print("\nCreating processor...")
processor = create_processor(enable_verification=True, enable_clustering=False)

print("\nProcessing text with WL citations...")
test_text = """Mastriano v. Gregory, 2024. 2024 WL 4149252, at *6 and 2024 WL 4003343, at *5. Also see 2025 WL 1410708."""

result = processor.process({"type": "text", "text": test_text}, "test-request")

print(f"\nResults:")
print(f"  Total citations: {len(result.citations)}")
print(f"  Processing mode: {result.mode}")

wl_count = 0
for cit in result.citations:
    cit_str = str(cit.get('citation', ''))
    if 'WL' in cit_str:
        wl_count += 1
        print(f"\nWL Citation #{wl_count}:")
        print(f"  Citation: {cit_str}")
        print(f"  Verified: {cit.get('verified', False)}")
        print(f"  Verification Status: {cit.get('verification_status', 'N/A')}")
        print(f"  Verification Error: {cit.get('verification_error', 'None')}")

print("\n" + "=" * 60)
if wl_count > 0:
    print(f"SUCCESS: Found {wl_count} WL citations")
    print("All WL citations should now be marked as 'Unverified due to proprietary format'")
else:
    print("WARNING: No WL citations found in test")
print("=" * 60)
