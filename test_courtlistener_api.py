#!/usr/bin/env python3
"""
CourtListener API Test
Test CourtListener integration to identify canonical data issues
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_courtlistener_api():
    """Test CourtListener API integration."""
    print("🔍 COURTLISTENER API TEST")
    print("="*50)
    
    try:
        # Check config loading
        from src.config import get_config_value
        
        api_key = get_config_value("COURTLISTENER_API_KEY", "")
        print(f"API Key from config: {'[PRESENT]' if api_key else '[MISSING]'}")
        
        if not api_key:
            print("❌ No CourtListener API key found in configuration")
            print("   This explains why canonical data is not being retrieved")
            print("   Location: src/config.json -> COURTLISTENER_API_KEY")
            return False
        
        # Test API call with the key
        print(f"\nTesting CourtListener API with key...")
        from src.courtlistener_verification import verify_with_courtlistener
        
        test_citation = "347 U.S. 483"
        test_case_name = "Brown v. Board of Education"
        
        print(f"Testing citation: {test_citation}")
        print(f"Expected case: {test_case_name}")
        
        result = verify_with_courtlistener(api_key, test_citation, extracted_case_name=test_case_name)
        
        print(f"\nAPI Response:")
        print(f"  Verified: {result.get('verified', False)}")
        print(f"  Canonical Name: {result.get('canonical_name', 'None')}")
        print(f"  Canonical Date: {result.get('canonical_date', 'None')}")
        print(f"  Canonical URL: {result.get('canonical_url', 'None')}")
        
        if result.get('verified'):
            print("✅ CourtListener API is working correctly")
            return True
        else:
            print("❌ CourtListener API call failed or returned no results")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ CourtListener API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """Test configuration loading."""
    print("\n🔧 CONFIG LOADING TEST")
    print("="*30)
    
    try:
        from src.config import get_config_value
        
        # Test different ways the API key might be stored
        keys_to_check = [
            "COURTLISTENER_API_KEY",
            "courtlistener_api_key", 
            "COURTLISTENER_TOKEN",
            "courtlistener_token"
        ]
        
        for key in keys_to_check:
            value = get_config_value(key, "")
            status = "✅ FOUND" if value else "❌ MISSING"
            print(f"  {status} {key}: {'[PRESENT]' if value else '[EMPTY]'}")
        
        # Check if environment variable is set
        import os
        env_key = os.environ.get('COURTLISTENER_API_KEY', '')
        print(f"  {'✅ FOUND' if env_key else '❌ MISSING'} Environment COURTLISTENER_API_KEY: {'[PRESENT]' if env_key else '[EMPTY]'}")
        
        return bool(any(get_config_value(key, "") for key in keys_to_check) or env_key)
        
    except Exception as e:
        print(f"❌ Config loading test failed: {e}")
        return False

def main():
    """Run CourtListener API tests."""
    print("🧪 COURTLISTENER CANONICAL DATA DIAGNOSIS")
    print("="*60)
    
    config_ok = test_config_loading()
    api_ok = test_courtlistener_api() if config_ok else False
    
    print(f"\n" + "="*60)
    print("📊 DIAGNOSIS RESULTS")
    print("="*60)
    
    if not config_ok:
        print("🔍 ROOT CAUSE: Missing CourtListener API Key")
        print("   The canonical data issue is caused by missing API credentials")
        print("   Solution: Add a valid CourtListener API key to src/config.json")
        print("   Field: COURTLISTENER_API_KEY")
    elif not api_ok:
        print("🔍 ROOT CAUSE: CourtListener API Issues")
        print("   API key is present but API calls are failing")
        print("   This could be due to:")
        print("   - Invalid API key")
        print("   - API rate limiting")
        print("   - Network connectivity issues")
        print("   - API endpoint changes")
    else:
        print("✅ CourtListener integration is working correctly")
        print("   Canonical data should be available")
    
    return config_ok and api_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
