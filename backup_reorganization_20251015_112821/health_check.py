import requests

def check_health():
    try:
        # Try to access the health check endpoint
        response = requests.get('http://localhost:5000/health', timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Backend service is running and healthy")
        else:
            print("❌ Backend service returned non-200 status code")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to backend service: {e}")
        print("\nPossible issues:")
        print("1. The backend service might not be running")
        print("2. The service might be running on a different port")
        print("3. There might be a network/firewall issue")
        print("\nTry running './cslaunch' to start the services")

if __name__ == "__main__":
    print("Checking backend service health...")
    check_health()
