#!/usr/bin/env python3
import sys
import requests

if len(sys.argv) < 2:
    print("Usage: ping_health.py <health_url>")
    sys.exit(2)

url = sys.argv[1]
try:
    r = requests.get(url, timeout=20, verify=False)
    print(f"STATUS={r.status_code}")
    print(r.text[:800])
    sys.exit(0 if r.status_code == 200 else 1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
