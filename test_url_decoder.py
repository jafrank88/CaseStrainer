#!/usr/bin/env python3
"""
Test script for URL decoder functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from url_decoder import URLDecoder, decode_and_clean_url

def test_url_decoder():
    """Test the URL decoder with various encoded URLs"""
    
    print("🧪 Testing URL Decoder")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Microsoft Defender URL",
            "url": "https://urldefense.com/v3/__https://case.law/caselaw/?reporter=cal-4th%26volume=11%26case=0001-01__;!!K-Hz7m0Vt54!lcqn6knCAosua6gJk8AC4Q-17TrHwdDGnxO86ki22fEQBKpNSGM5q48EYTTPvEFv1lxsoN7NKcodFOvFuXI$",
            "expected": "https://case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01"
        },
        {
            "name": "Google Safe Browsing URL",
            "url": "https://safebrowsing.google.com/safebrowsing/diagnostic?site=https%3A//case.law/caselaw/%3Freporter%3Dcal-4th%26volume%3D11%26case%3D0001-01",
            "expected": "https://case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01"
        },
        {
            "name": "Office 365 Safe Links URL",
            "url": "https://nam12.safelinks.protection.outlook.com/?url=https%3A%2F%2Fcase.law%2Fcaselaw%2F%3Freporter%3Dcal-4th%26volume%3D11%26case%3D0001-01&data=05%7C01%7C",
            "expected": "https://case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01"
        },
        {
            "name": "Normal URL (should not be decoded)",
            "url": "https://case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01",
            "expected": "https://case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01"
        },
        {
            "name": "URL without protocol (should be cleaned)",
            "url": "case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01",
            "expected": "https://case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Input: {test_case['url'][:80]}...")
        
        try:
            # Test the main decode function
            cleaned_url, was_decoded, original_url = decode_and_clean_url(test_case['url'])
            
            print(f"   Decoded: {was_decoded}")
            print(f"   Output: {cleaned_url}")
            print(f"   Expected: {test_case['expected']}")
            
            # Check if the result matches expected
            if cleaned_url == test_case['expected']:
                print("   ✅ PASS")
                passed += 1
            else:
                print("   ❌ FAIL - Output doesn't match expected")
                failed += 1
                
        except Exception as e:
            print(f"   ❌ FAIL - Exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed!")
        return False

def test_url_detection():
    """Test URL encoding detection"""
    
    print("\n🔍 Testing URL Encoding Detection")
    print("=" * 50)
    
    test_urls = [
        "https://urldefense.com/v3/__https://example.com__;!!hash$",
        "https://safebrowsing.google.com/safebrowsing/diagnostic?site=example.com",
        "https://nam12.safelinks.protection.outlook.com/?url=example.com",
        "https://example.com/normal/url",
        "https://case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01"
    ]
    
    for url in test_urls:
        is_encoded = URLDecoder.is_encoded_url(url)
        print(f"{'🔒' if is_encoded else '🔓'} {url[:60]}... -> {'Encoded' if is_encoded else 'Normal'}")

if __name__ == "__main__":
    success = test_url_decoder()
    test_url_detection()
    
    if success:
        print("\n✅ URL decoder is working correctly!")
        print("Users can now paste Microsoft Defender and other encoded URLs directly into CaseStrainer.")
    else:
        print("\n❌ URL decoder needs fixes!")
        sys.exit(1) 