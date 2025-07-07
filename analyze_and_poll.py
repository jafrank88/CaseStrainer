#!/usr/bin/env python3
print('[DEBUG] Script started')
"""
Submit text to /casestrainer/api/analyze and poll /casestrainer/api/task_status/<task_id> for results.
Timeout: 60s for short text (<=200 chars), 120s for longer.
"""

import requests
import time
import sys
import json

def analyze_and_poll(text_to_analyze):
    api_base = "http://localhost:5000/casestrainer/api"
    analyze_url = f"{api_base}/analyze"
    print(f"Submitting text to: {analyze_url}")
    print(f"Text: {text_to_analyze!r}")

    # Decide timeout
    timeout = 60 if len(text_to_analyze) <= 200 else 120
    print(f"Polling timeout: {timeout} seconds")

    # Submit for analysis
    try:
        print("[DEBUG] Sending POST to /analyze...")
        resp = requests.post(analyze_url, json={"type": "text", "text": text_to_analyze}, timeout=30)
        print(f"[DEBUG] Response status: {resp.status_code}")
        print(f"[DEBUG] Response text: {resp.text}")
        resp.raise_for_status()
        data = resp.json()
        print(f"[DEBUG] Response JSON: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"❌ Error submitting to /analyze: {e}")
        sys.exit(1)

    # If completed immediately
    if data.get("status") == "completed":
        print("✅ Analysis completed immediately:")
        print(json.dumps(data, indent=2))
        return

    # If async, poll for result
    if data.get("status") == "processing" and data.get("task_id"):
        task_id = data["task_id"]
        print(f"Task queued. Polling for result (task_id={task_id})...")
        status_url = f"{api_base}/task_status/{task_id}"
        start = time.time()
        while True:
            try:
                print(f"[DEBUG] Polling {status_url}")
                status_resp = requests.get(status_url, timeout=10)
                print(f"[DEBUG] Poll status: {status_resp.status_code}")
                print(f"[DEBUG] Poll response: {status_resp.text}")
                status_data = status_resp.json()
            except Exception as e:
                print(f"❌ Error polling task status: {e}")
                break
            if status_data.get("status") == "completed":
                print("✅ Analysis completed:")
                print(json.dumps(status_data, indent=2))
                break
            elif status_data.get("status") == "error":
                print(f"❌ Error in analysis: {status_data.get('message')}")
                break
            elapsed = time.time() - start
            if elapsed > timeout:
                print(f"⏰ Timeout after {timeout} seconds. Last status:")
                print(json.dumps(status_data, indent=2))
                break
            print(f"... still processing ({int(elapsed)}s elapsed)")
            time.sleep(2)
    else:
        print(f"❌ Unexpected response from /analyze: {data}")

if __name__ == "__main__":
    # Example usage: pass text as argument or edit below
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "See State v. Lewis, 115 Wn.2d 294, 298-99, 797 P.2d 1141 (1990)."
    analyze_and_poll(text) 