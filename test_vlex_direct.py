#!/usr/bin/env python3
"""
Test VLex verification with known case name
"""

import asyncio
from src.unified_verification_master import UnifiedVerificationMaster

async def test_vlex_with_case_name():
    """Test VLex verification with the specific citation and case name"""
    
    # Create verifier
    verifier = UnifiedVerificationMaster()
    
    print("=" * 80)
    print("TESTING VLEX WITH CASE NAME")
    print("=" * 80)
    print()
    
    # Test with the known case name from the user's example
    citation = "146 F.4th 165"
    case_name = "Giuffre v. Maxwell"
    
    print(f"Testing citation: {citation}")
    print(f"With case name: {case_name}")
    print("-" * 40)
    
    # Test with VLex directly
    result = await verifier._verify_with_vlex(
        citation=citation,
        extracted_case_name=case_name,
        extracted_date=None,
        timeout=10.0
    )
    
    print(f"Verified: {result.verified}")
    print(f"Possible Match: {getattr(result, 'possible_match', False)}")
    print(f"Canonical Name: {result.canonical_name}")
    print(f"Canonical Date: {result.canonical_date}")
    print(f"URL: {result.canonical_url}")
    print(f"Source: {result.source}")
    print(f"Method: {getattr(result, 'method', 'N/A')}")
    print(f"Error: {result.error}")
    print()
    
    # Also test the direct URL we know exists
    print("=" * 80)
    print("TESTING DIRECT VLEX URL")
    print("=" * 80)
    print()
    
    import requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    url = "https://case-law.vlex.com/vid/giuffre-v-maxwell-1093577203"
    print(f"Checking: {url}")
    
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.text
        # Check if citation is in the page
        if "146 F.4th 165" in content:
            print("✅ Citation found on page!")
        else:
            print("❌ Citation not found on page")
        
        # Extract title
        import re
        title_match = re.search(r'<title>([^<]+)</title>', content)
        if title_match:
            print(f"Title: {title_match.group(1)}")

if __name__ == "__main__":
    asyncio.run(test_vlex_with_case_name())
