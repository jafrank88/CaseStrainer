#!/usr/bin/env python3
"""
Check CourtListener API key configuration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def check_api_key():
    """Check the CourtListener API key"""
    
    print("=== Checking CourtListener API Key ===")
    
    # Try different ways to get the API key
    api_key = None
    
    # Method 1: Direct from config
    try:
        from config import COURTLISTENER_API_KEY
        api_key = COURTLISTENER_API_KEY
        print(f"1. From config.py: {api_key[:10] if api_key else 'Not set'}...")
    except Exception as e:
        print(f"1. Error getting from config.py: {e}")
    
    # Method 2: From environment variable
    env_key = os.environ.get('COURTLISTENER_API_KEY')
    print(f"2. From environment: {env_key[:10] if env_key else 'Not set'}...")
    
    # Method 3: From get_config_value function
    try:
        from config import get_config_value
        config_key = get_config_value("COURTLISTENER_API_KEY")
        print(f"3. From get_config_value: {config_key[:10] if config_key else 'Not set'}...")
    except Exception as e:
        print(f"3. Error getting from get_config_value: {e}")
    
    # Check if any key starts with 443a
    all_keys = [api_key, env_key, config_key]
    valid_keys = [k for k in all_keys if k and k.startswith("443a")]
    
    print(f"\n=== Results ===")
    if valid_keys:
        print(f"✅ Found {len(valid_keys)} valid API key(s) starting with '443a'")
        for i, key in enumerate(valid_keys):
            print(f"   Key {i+1}: {key[:10]}...")
    else:
        print(f"❌ No API keys found starting with '443a'")
        print(f"   Available keys:")
        for i, key in enumerate(all_keys):
            if key:
                print(f"     Key {i+1}: {key[:10]}...")
            else:
                print(f"     Key {i+1}: Not set")

if __name__ == '__main__':
    check_api_key() 