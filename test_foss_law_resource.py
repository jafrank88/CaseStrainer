#!/usr/bin/env python3
"""
Test if Foss case verification reaches law.resource.org
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.unified_verification_master import UnifiedVerificationMaster

async def test_foss_law_resource():
    """Test if Foss case verification reaches law.resource.org"""
    
    print("🔍 TESTING FOSS CASE LAW.RESOURCE.ORG ACCESS")
    print("=" * 60)
    
    foss_citation = "161 F.3d 584"
    
    # Create verifier with detailed logging
    verifier = UnifiedVerificationMaster()
    
    print(f"📋 Testing citation: {foss_citation}")
    print()
    
    # Test 1: Direct law.resource.org URL check
    print("--- Test 1: Direct law.resource.org URL ---")
    import requests
    
    # Try the exact URL pattern from the debug script
    # Note: The correct pattern seems to be /pub/us/case/reporter/ not /pub/us/code/report/
    direct_url = "https://law.resource.org/pub/us/case/reporter/F3/161/F3d.584.97-36097.html"
    print(f"URL: {direct_url}")
    
    try:
        response = requests.get(direct_url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            if "Foss" in content and "Marine Fisheries" in content:
                print("✅ Foss case found at law.resource.org")
                # Extract the actual case name
                import re
                title_match = re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE)
                if title_match:
                    print(f"Title: {title_match.group(1)}")
            else:
                print("❌ Foss case content not found at law.resource.org")
                print(f"Content preview: {content[:200]}...")
        else:
            print(f"❌ Failed to access law.resource.org: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing law.resource.org: {e}")
    
    print()
    
    # Test 2: Try the directory listing approach
    print("--- Test 2: Directory listing approach ---")
    directory_url = "https://law.resource.org/pub/us/case/reporter/F3/161/"
    print(f"Directory URL: {directory_url}")
    
    try:
        response = requests.get(directory_url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            # Look for files containing "584"
            if "584" in content:
                print("✅ Found files containing page 584")
                # Extract file links
                import re
                file_pattern = r'<a href="([^"]*584[^"]*)"[^>]*>([^<]*584[^<]*)</a>'
                matches = re.findall(file_pattern, content, re.IGNORECASE)
                for filename, title in matches:
                    print(f"  File: {filename} - {title}")
            else:
                print("❌ No files containing page 584 found")
        else:
            print(f"❌ Failed to access directory: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing directory: {e}")
    
    print()
    
    # Test 3: Use the verification system directly
    print("--- Test 3: Verification system with law.resource.org ---")
    
    # Enable debug logging to see the process
    import logging
    logging.basicConfig(level=logging.INFO)
    
    result = verifier.verify_citation_sync(
        foss_citation,
        None,  # No case name to force fallback
        None
    )
    
    print(f"Verification result:")
    print(f"  Verified: {result.verified}")
    print(f"  Source: {result.source}")
    print(f"  Canonical name: {result.canonical_name}")
    print(f"  Error: {result.error}")
    
    # Check if law.resource.org was tried
    if result.error and "law.resource.org" in result.error.lower():
        print("✅ Law Resource.org was attempted but failed")
    elif result.source == "Law Resource.org":
        print("✅ Law Resource.org succeeded!")
    elif "law.resource.org" in str(result.source).lower():
        print("✅ Law Resource.org was involved in verification")
    else:
        print("❌ Law Resource.org was not tried")
    
    print()
    
    # Test 4: Try with case name to see if that helps
    print("--- Test 4: With case name provided ---")
    
    result2 = verifier.verify_citation_sync(
        foss_citation,
        "Foss v. National Marine Fisheries Service",
        "1998"
    )
    
    print(f"Verification with case name:")
    print(f"  Verified: {result2.verified}")
    print(f"  Source: {result2.source}")
    print(f"  Canonical name: {result2.canonical_name}")
    
    if result2.source == "Law Resource.org":
        print("✅ Law Resource.org found the case with name provided!")
    elif result2.verified:
        print(f"✅ Case verified via: {result2.source}")
    else:
        print(f"❌ Verification failed: {result2.error}")

if __name__ == "__main__":
    asyncio.run(test_foss_law_resource())
