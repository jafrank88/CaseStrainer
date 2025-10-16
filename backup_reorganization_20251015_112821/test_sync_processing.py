"""
Test sync processing pathway
"""
import requests
import json

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = "https://wolf.law.uw.edu/casestrainer/api"

# Small text for sync processing (< 5KB triggers sync)
small_text = """
See Erie Railroad Co. v. Tompkins, 304 U.S. 64 (1938).
Compare United States v. Nixon, 418 U.S. 683 (1974).
Citing Marbury v. Madison, 5 U.S. 137 (1803).
"""

print("=" * 60)
print("TESTING SYNC PROCESSING")
print("=" * 60)
print(f"\nText size: {len(small_text)} bytes (should trigger SYNC)")
print(f"Expected: Immediate response with citations")

try:
    response = requests.post(
        f"{base_url}/analyze",
        json={
            "type": "text",
            "text": small_text,
            "client_request_id": "sync-test-123"
        },
        timeout=30,
        verify=False
    )
    
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\n✅ SUCCESS - Sync processing working!")
        print(f"\nProcessing mode: {result.get('metadata', {}).get('processing_mode')}")
        print(f"Citations found: {len(result.get('citations', []))}")
        print(f"Processing time: {result.get('processing_time_ms')}ms")
        
        if result.get('citations'):
            print(f"\nFirst citation:")
            print(f"  {result['citations'][0].get('citation')}")
            print(f"  Case: {result['citations'][0].get('extracted_case_name', 'N/A')}")
        
        if result.get('metadata', {}).get('processing_mode') == 'immediate':
            print(f"\n✅ CONFIRMED: Sync processing used (immediate mode)")
        else:
            print(f"\n⚠️  Processing mode: {result.get('metadata', {}).get('processing_mode')}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
