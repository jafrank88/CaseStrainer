print("=== Simple Test ===")
print("This is a test")

# Test basic requests
import requests

print(f"Requests version: {requests.__version__}")

# Try a simple request
try:
    response = requests.get("https://httpbin.org/get")
    print(f"Test request status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
