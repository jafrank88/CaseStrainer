#!/usr/bin/env python3
"""
Simple test to verify API key loading from config.env
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_config_loading():
    """Test if API key is loaded correctly."""
    
    print("=== Config Loading Test ===")
    
    # Test 1: Check if config.env exists
    config_env_path = os.path.join(os.path.dirname(__file__), 'config.env')
    print(f"1. config.env path: {config_env_path}")
    print(f"   Exists: {os.path.exists(config_env_path)}")
    
    if os.path.exists(config_env_path):
        with open(config_env_path, 'r') as f:
            content = f.read()
            has_api_key = 'COURTLISTENER_API_KEY' in content
            print(f"   Contains COURTLISTENER_API_KEY: {has_api_key}")
    
    # Test 2: Check environment variable directly
    env_key = os.environ.get('COURTLISTENER_API_KEY')
    print(f"2. Environment variable: {env_key[:8] + '...' if env_key else 'None'}")
    
    # Test 3: Import and test config system
    try:
        from config import get_config_value
        config_key = get_config_value('COURTLISTENER_API_KEY')
        print(f"3. get_config_value result: {config_key[:8] + '...' if config_key else 'None'}")
        
        if config_key and config_key.startswith('443a'):
            print("✅ API key loaded successfully!")
            return True
        else:
            print("❌ API key not loaded or incorrect format")
            return False
            
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False

if __name__ == '__main__':
    success = test_config_loading()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
