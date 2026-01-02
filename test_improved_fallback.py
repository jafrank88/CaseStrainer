#!/usr/bin/env python3
"""
Test the improved calculated fallback verification
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.fast_verification_system import FastVerificationSystem

async def test_improved_fallback():
    """Test the improved calculated fallback verification"""
    
    print("🧪 TESTING IMPROVED CALCULATED FALLBACK")
    print("=" * 60)
    
    foss_citation = "161 F.3d 584"
    
    # Create fast verifier
    verifier = FastVerificationSystem(enable_web_verification=False)  # Disable web to force fallback
    
    print(f"📋 Testing citation: {foss_citation}")
    print()
    
    # Test 1: No case name (should trigger lookup)
    print("--- Test 1: No case name (should trigger lookup) ---")
    result1 = await verifier.verify_citation_async(
        foss_citation,
        None,  # No case name extracted
        None,  # No date extracted
        timeout=10.0
    )
    
    print(f"Verified: {result1.get('verified', False)}")
    print(f"Source: {result1.get('source', 'N/A')}")
    print(f"Canonical: {result1.get('canonical_name', 'N/A')}")
    print(f"Date: {result1.get('canonical_date', 'N/A')}")
    print(f"Confidence: {result1.get('confidence', 0):.2f}")
    print(f"Note: {result1.get('note', 'N/A')}")
    print()
    
    # Test 2: With fallback case name
    print("--- Test 2: With fallback case name ---")
    result2 = await verifier.verify_citation_async(
        foss_citation,
        "Federal Appeals Case",  # Fallback name
        None,
        timeout=10.0
    )
    
    print(f"Verified: {result2.get('verified', False)}")
    print(f"Source: {result2.get('source', 'N/A')}")
    print(f"Canonical: {result2.get('canonical_name', 'N/A')}")
    print(f"Date: {result2.get('canonical_date', 'N/A')}")
    print(f"Confidence: {result2.get('confidence', 0):.2f}")
    print(f"Note: {result2.get('note', 'N/A')}")
    print()
    
    # Test 3: Direct CourtListener API check
    print("--- Test 3: Direct CourtListener API check ---")
    try:
        import requests
        from src.config import get_config_value
        
        api_key = get_config_value("COURTLISTENER_API_KEY", "")
        headers = {}
        if api_key:
            headers["Authorization"] = f"Token {api_key}"
            headers["Content-Type"] = "application/json"
        
        api_url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        data = {"text": foss_citation}
        
        response = requests.post(api_url, headers=headers, json=data, timeout=5.0)
        print(f"API status: {response.status_code}")
        
        if response.status_code == 200:
            result_data = response.json()
            print(f"Results found: {len(result_data)}")
            if result_data:
                result = result_data[0]
                print(f"Case name: {result.get('case_name', 'N/A')}")
                print(f"Date: {result.get('date', 'N/A')}")
                print(f"URL: {result.get('url', 'N/A')}")
        else:
            print(f"❌ API request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking API: {e}")
    
    print()
    
    # Analysis
    print("🔍 ANALYSIS:")
    print(f"1. Test 1 (no name) found: {result1.get('canonical_name', 'N/A')}")
    print(f"2. Test 2 (fallback name) found: {result2.get('canonical_name', 'N/A')}")
    
    if (result1.get('canonical_name') and 
        result1.get('canonical_name') != 'N/A' and 
        result1.get('canonical_name') != 'Federal Appeals Case'):
        print("✅ SUCCESS: Found actual case name without extraction!")
    else:
        print("❌ Still not finding actual case name")
        if result1.get('source') == 'calculated_fallback':
            print("   - Still using basic fallback (no lookup)")
        elif result1.get('source') == 'calculated_fallback_with_lookup':
            print("   - Lookup attempted but didn't find the case")

if __name__ == "__main__":
    asyncio.run(test_improved_fallback())
