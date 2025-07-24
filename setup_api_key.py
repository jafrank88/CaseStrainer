#!/usr/bin/env python3
"""
Setup script for CourtListener API key
"""

import os
import json
import sys

# Prevent use of v3 CourtListener API endpoints
if 'v3' in url:
    print("ERROR: v3 CourtListener API endpoint detected. Please use v4 only.")
    sys.exit(1)

def setup_courtlistener_api_key():
    """Setup the CourtListener API key"""
    print("🔑 CourtListener API Key Setup")
    print("=" * 40)
    
    # Check if API key is already set
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if api_key and api_key != "443a1234567890abcdef1234567890abcdef1234":
        print(f"✅ API key already set: {api_key[:10]}...")
        return True
    
    print("To get a CourtListener API key:")
    print("1. Go to https://www.courtlistener.com/api/rest-info/")
    print("2. Sign up for an account")
    print("3. Request an API key")
    print("4. Copy your API key")
    print()
    
    # Get API key from user
    api_key = input("Enter your CourtListener API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⚠️  No API key provided. Verification will be limited.")
        return False
    
    # Validate API key format
    if not api_key.startswith("443a"):
        print("⚠️  Warning: API key doesn't start with expected prefix '443a'")
        print("   This might not be a valid CourtListener API key.")
        continue_anyway = input("Continue anyway? (y/N): ").strip().lower()
        if continue_anyway != 'y':
            return False
    
    # Set environment variable
    os.environ['COURTLISTENER_API_KEY'] = api_key
    print(f"✅ API key set: {api_key[:10]}...")
    
    # Update config.env file
    config_env_path = "config.env"
    if os.path.exists(config_env_path):
        with open(config_env_path, 'r') as f:
            content = f.read()
        
        # Replace placeholder or add new line
        if "COURTLISTENER_API_KEY=" in content:
            content = content.replace("COURTLISTENER_API_KEY=your-courtlistener-api-key-here", f"COURTLISTENER_API_KEY={api_key}")
        else:
            content += f"\nCOURTLISTENER_API_KEY={api_key}"
        
        with open(config_env_path, 'w') as f:
            f.write(content)
        
        print("✅ Updated config.env file")
    
    return True

def test_api_key():
    """Test the API key"""
    print("\n🧪 Testing API Key")
    print("=" * 20)
    
    api_key = os.environ.get('COURTLISTENER_API_KEY')
    if not api_key:
        print("❌ No API key found")
        return False
    
    try:
        import requests
        
        # Test with a simple citation
        url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
        headers = {"Authorization": f"Token {api_key}"}
        data = {"citations": ["123 F.3d 456"]}
        
        print("Testing API connection...")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            print("✅ API key is valid!")
            return True
        elif response.status_code == 401:
            print("❌ API key is invalid")
            return False
        else:
            print(f"⚠️  API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

if __name__ == "__main__":
    if setup_courtlistener_api_key():
        test_api_key()
    else:
        print("Setup cancelled.") 