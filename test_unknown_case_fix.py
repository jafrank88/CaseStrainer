"""
Test the N/A to Unknown Case fixes
"""

import sys
sys.path.insert(0, 'D:/dev/casestrainer/src')

from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2

print("TESTING N/A TO UNKNOWN CASE FIX")
print("=" * 60)

# Test cases that should now show "Unknown Case, [citation]"
test_cases = [
    "2024 WL 4003343",
    "346 F.R.D. 102", 
    "732 F.2d 1302",
    "2006 WL 2788256",
    "2022 WL 15153410"
]

processor = UnifiedCitationProcessorV2()

for text in test_cases:
    print(f"\nTesting: {text}")
    print("-" * 40)
    
    citations = processor.process_text(text)
    
    if citations:
        cit = citations[0]
        print(f"Result: '{cit.extracted_case_name}'")
        
        if cit.extracted_case_name.startswith("Unknown Case"):
            print("✅ SUCCESS: Using Unknown Case format")
        else:
            print("❌ FAIL: Still using old format")

print("\n" + "=" * 60)
print("NOTE: These changes require a server restart to take effect in production")
