import urllib.request
import urllib.error

url = 'http://casestrainer-nginx-prod/casestrainer/api/health'
print(f"Testing: {url}")

try:
    response = urllib.request.urlopen(url, timeout=5)
    print(f"✅ Success! Status: {response.status}")
    print(f"Response: {response.read()[:200]}")
except urllib.error.URLError as e:
    print(f"❌ URLError: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
