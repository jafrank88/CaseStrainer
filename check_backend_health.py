#!/usr/bin/env python3
"""
Check backend health
"""

import requests

def check_health():
    """Check backend health"""
    
    base_url = "https://wolf.law.uw.edu/casestrainer/api"
    
    print(f"Checking backend health...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        
        print(f"Health check status: {response.status_code}")
        
        if response.status_code == 200:
            health = response.json()
            print(f"Health response: {health}")
            print(f"✅ Backend is healthy")
        else:
            print(f"❌ Backend unhealthy: {response.text}")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    check_health()
