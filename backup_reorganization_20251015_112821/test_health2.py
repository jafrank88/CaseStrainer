import urllib.request
import urllib.error

url = 'http://casestrainer-backend-prod:5000/casestrainer/api/health'
print(f"Testing: {url}")

try:
    response = urllib.request.urlopen(url, timeout=5)
    print(f"✅ Success! Status: {response.status}")
    data = response.read()
    print(f"Response length: {len(data)} bytes")
except urllib.error.URLError as e:
    print(f"❌ URLError: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
