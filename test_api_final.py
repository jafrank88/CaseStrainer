#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final test to check if API key is loaded and working.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_api_key_final():
    """Final test of API key loading and basic functionality."""
    
    print("Final API Key Test")
    print("=" * 20)
    
    try:
        # Test 1: Check if config.env exists
        config_env_path = os.path.join(os.path.dirname(__file__), 'config.env')
        if os.path.exists(config_env_path):
            print(f"✅ config.env exists at: {config_env_path}")
        else:
            print(f"❌ config.env not found at: {config_env_path}")
            return False
        
        # Test 2: Import config system
        from config import get_config_value
        print("✅ Config system imported")
        
        # Test 3: Get API key
        api_key = get_config_value("COURTLISTENER_API_KEY")
        
        if api_key:
            print(f"✅ API key loaded: {api_key[:8]}...")
            
            if api_key.startswith("443a"):
                print("✅ API key format correct")
                
                # Test 4: Simple HTTP test
                import requests
                
                url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
                headers = {
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json"
                }
                data = {"citation": "100 Wn.2d 212"}
                
                print("Testing API call...")
                response = requests.post(url, json=data, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    print("✅ API call successful!")
                    result = response.json()
                    
                    if isinstance(result, list) and len(result) > 0:
                        first_result = result[0]
                        clusters = first_result.get('clusters', [])
                        
                        if clusters:
                            case_name = clusters[0].get('case_name', 'N/A')
                            print(f"Found case: {case_name}")
                            
                            if "Seattle" in case_name and "Ratliff" in case_name:
                                print("✅ Correct case found!")
                                return True
                            else:
                                print("⚠️  Different case found")
                        else:
                            print("⚠️  No clusters in result")
                    else:
                        print("⚠️  Empty or invalid result")
                        
                elif response.status_code == 401:
                    print("❌ Authentication failed")
                elif response.status_code == 404:
                    print("⚠️  Citation not found")
                else:
                    print(f"❌ API error: {response.status_code}")
                    
            else:
                print(f"❌ API key format wrong: {api_key[:8]}")
        else:
            print("❌ No API key loaded")
            
            # Debug: Check environment directly
            env_key = os.environ.get("COURTLISTENER_API_KEY")
            if env_key:
                print(f"Found in env: {env_key[:8]}...")
            else:
                print("Not in environment either")
        
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == '__main__':
    success = test_api_final()
    print(f"\nResult: {'✅ SUCCESS' if success else '❌ FAILED'}")
