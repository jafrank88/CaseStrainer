#!/usr/bin/env python3
import requests

print("Testing production server...")
try:
    response = requests.get("https://wolf.law.uw.edu/casestrainer/api/health", timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Server is accessible")
        data = response.json()
        print(f"Version: {data.get('version', 'unknown')}")
    else:
        print(f"❌ Server error: {response.text[:100]}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
