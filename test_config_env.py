#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test if the API key is being loaded from config.env correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config_loading():
    """Test if the API key loads from config.env."""
    
    print("Configuration Loading Test")
    print("=" * 30)
    
    try:
        # Import the config system
        from config import get_config_value
        
        print("✅ Successfully imported config system")
        
        # Test API key loading
        api_key = get_config_value("COURTLISTENER_API_KEY")
        
        if api_key:
            print(f"✅ API key loaded successfully: {api_key[:8]}...")
            print(f"   Full length: {len(api_key)} characters")
            
            if api_key.startswith("443a"):
                print("✅ API key format looks correct (starts with 443a)")
                return True
            else:
                print(f"⚠️  API key doesn't start with expected '443a': {api_key[:8]}")
                return False
        else:
            print("❌ No API key found")
            print("Checking environment variables directly...")
            
            # Check if it's in environment variables
            env_key = os.environ.get("COURTLISTENER_API_KEY")
            if env_key:
                print(f"✅ Found in environment: {env_key[:8]}...")
            else:
                print("❌ Not found in environment variables either")
            
            return False
            
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_verification():
    """Test simple CourtListener verification."""
    
    print("\nSimple Verification Test")
    print("=" * 25)
    
    try:
        from config import get_config_value
        
        api_key = get_config_value("COURTLISTENER_API_KEY")
        if not api_key:
            print("❌ No API key available for verification test")
            return False
        
        print(f"Using API key: {api_key[:8]}...")
        
        # Test with a simple HTTP request to CourtListener
        import requests
        
        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }
        
        # Test with City of Seattle v. Ratliff citation
        test_citation = "100 Wn.2d 212"
        data = {"citation": test_citation}
        
        print(f"Testing citation: {test_citation}")
        print("Making API request...")
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API request successful!")
            
            try:
                result = response.json()
                print(f"Response type: {type(result)}")
                
                if isinstance(result, list) and len(result) > 0:
                    first_result = result[0]
                    print(f"First result keys: {list(first_result.keys()) if isinstance(first_result, dict) else 'Not a dict'}")
                    
                    # Look for canonical name in the result
                    if isinstance(first_result, dict):
                        clusters = first_result.get('clusters', [])
                        if clusters and len(clusters) > 0:
                            cluster = clusters[0]
                            case_name = cluster.get('case_name')
                            date_filed = cluster.get('date_filed')
                            
                            print(f"Case name: {case_name}")
                            print(f"Date filed: {date_filed}")
                            
                            if case_name and "Seattle" in case_name and "Ratliff" in case_name:
                                print("✅ Found correct case name!")
                                return True
                            else:
                                print("⚠️  Case name doesn't match expected")
                        else:
                            print("⚠️  No clusters found in result")
                else:
                    print(f"⚠️  Unexpected result format: {result}")
                    
            except Exception as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response: {response.text[:200]}...")
                
        elif response.status_code == 401:
            print("❌ Authentication failed - API key may be invalid")
        elif response.status_code == 404:
            print("⚠️  Citation not found in CourtListener database")
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
        return False
        
    except Exception as e:
        print(f"❌ Verification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing config.env API Key Loading")
    print("=" * 40)
    
    config_ok = test_config_loading()
    
    if config_ok:
        verification_ok = test_simple_verification()
        
        print("\n" + "=" * 40)
        print("SUMMARY:")
        print(f"Config Loading: {'✅' if config_ok else '❌'}")
        print(f"API Verification: {'✅' if verification_ok else '❌'}")
        
        if config_ok and verification_ok:
            print("\n🎉 API key is working correctly!")
            print("The canonical name/date issue should now be resolved.")
        else:
            print("\n⚠️  Some issues remain to be fixed.")
    else:
        print("\n❌ Cannot test verification without valid API key.")
