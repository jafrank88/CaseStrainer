#!/usr/bin/env python3
import sys
import json
import requests

if len(sys.argv) < 2:
    print("Usage: ping_analyze.py <base_url>")
    sys.exit(2)

base = sys.argv[1].rstrip('/')
url = f"{base}/analyze"

payload = {"type": "text", "text": "Ping from diagnostics"}
try:
    r = requests.post(url, json=payload, timeout=30, verify=False)
    print(f"STATUS={r.status_code}")
    ct = r.headers.get('Content-Type', '')
    print(f"Content-Type={ct}")
    body = r.text
    print(body[:800])
    sys.exit(0 if r.status_code == 200 else 1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
