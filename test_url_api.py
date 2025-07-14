import requests
import json

def test_url_api():
    base_url = "http://localhost:5001/casestrainer/api"
    
    # Test URL endpoint
    print("Testing URL endpoint...")
    try:
        # Test with a simple URL first
        data = {
            "type": "url",
            "url": "https://case.law/caselaw/?reporter=cal-4th&volume=11&case=0001-01"
        }
        response = requests.post(f"{base_url}/analyze", json=data)
        print(f"URL analyze status: {response.status_code}")
        print(f"URL analyze response: {response.json()}")
    except Exception as e:
        print(f"URL analyze test failed: {e}")
    
    # Test with the encoded URL
    print("\nTesting encoded URL endpoint...")
    try:
        encoded_url = "https://urldefense.com/v3/__https://case.law/caselaw/?reporter=cal-4th%26volume=11%26case=0001-01__;!!K-Hz7m0Vt54!lcqn6knCAosua6gJk8AC4Q-17TrHwdDGnxO86ki22fEQBKpNSGM5q48EYTTPvEFv1lxsoN7NKcodFOvFuXI$"
        data = {
            "type": "url",
            "url": encoded_url
        }
        response = requests.post(f"{base_url}/analyze", json=data)
        print(f"Encoded URL analyze status: {response.status_code}")
        print(f"Encoded URL analyze response: {response.json()}")
    except Exception as e:
        print(f"Encoded URL analyze test failed: {e}")

if __name__ == "__main__":
    test_url_api() 