import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from src.http.clients import build_default_headers
import json

if __name__ == "__main__":
    headers = build_default_headers(os.getenv('COURTLISTENER_API_KEY'))
    print(json.dumps(headers, ensure_ascii=False))
