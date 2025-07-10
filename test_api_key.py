#!/usr/bin/env python3
"""
Test script to verify CourtListener API key loading
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config import COURTLISTENER_API_KEY, get_config_value
    print("✅ Successfully imported config module")
    
    # Test direct import
    print(f"COURTLISTENER_API_KEY (direct): {COURTLISTENER_API_KEY}")
    print(f"COURTLISTENER_API_KEY length: {len(COURTLISTENER_API_KEY) if COURTLISTENER_API_KEY else 0}")
    
    # Test get_config_value function
    api_key_via_function = get_config_value("COURTLISTENER_API_KEY")
    print(f"COURTLISTENER_API_KEY (via function): {api_key_via_function}")
    
    # Test if it starts with expected prefix
    if COURTLISTENER_API_KEY and COURTLISTENER_API_KEY.startswith("443a"):
        print("✅ API key starts with expected prefix '443a'")
    else:
        print("❌ API key does not start with expected prefix '443a'")
    
    # Test if key is not empty
    if COURTLISTENER_API_KEY:
        print("✅ API key is set and not empty")
    else:
        print("❌ API key is empty or not set")
        
    # Test environment variable override
    env_key = os.environ.get("COURTLISTENER_API_KEY")
    if env_key:
        print(f"Environment variable COURTLISTENER_API_KEY: {env_key}")
    else:
        print("No environment variable COURTLISTENER_API_KEY set")
        
except ImportError as e:
    print(f"❌ Failed to import config: {e}")
except Exception as e:
    print(f"❌ Error during testing: {e}") 