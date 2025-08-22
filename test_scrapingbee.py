#!/usr/bin/env python3
"""
Test script for ScrapingBee integration
"""

import os
import asyncio
from src.enhanced_fallback_verifier import EnhancedFallbackVerifier

async def test_scrapingbee():
    """Test ScrapingBee verification with a Washington citation."""
    
    # Check if API key is configured
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        print("❌ SCRAPINGBEE_API_KEY not configured")
        print("Please set your ScrapingBee API key:")
        print("export SCRAPINGBEE_API_KEY=your_api_key_here")
        print("\nGet your free API key from: https://www.scrapingbee.com/")
        return
    
    print(f"✅ ScrapingBee API key configured: {api_key[:8]}...")
    
    # Test citation
    citation = "392 P.3d 1041"
    case_name = "In re Marriage of Black"
    year = "2017"
    
    print(f"\n🔍 Testing ScrapingBee with citation: {citation}")
    print(f"Case: {case_name}")
    print(f"Year: {year}")
    
    # Create verifier
    verifier = EnhancedFallbackVerifier()
    
    try:
        # Test ScrapingBee verification
        print("\n🚀 Starting ScrapingBee verification...")
        result = await verifier._verify_with_scrapingbee(
            citation_text=citation,
            citation_info={},
            extracted_case_name=case_name,
            extracted_date=year,
            search_query=f"{citation} {case_name} {year}"
        )
        
        if result:
            print("✅ ScrapingBee verification successful!")
            print(f"Source: {result.get('source')}")
            print(f"Case Name: {result.get('canonical_name')}")
            print(f"Year: {result.get('canonical_date')}")
            print(f"URL: {result.get('url')}")
            print(f"Confidence: {result.get('confidence')}")
        else:
            print("❌ ScrapingBee verification failed - no results found")
            
    except Exception as e:
        print(f"❌ ScrapingBee verification error: {e}")
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_scrapingbee())
