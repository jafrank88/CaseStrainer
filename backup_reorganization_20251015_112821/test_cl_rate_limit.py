"""
Test CourtListener API rate limit headers
"""
import urllib.request
import os

api_key = os.environ.get('COURTLISTENER_API_KEY', '***REDACTED_COURTLISTENER_KEY***')

print(f"API Key: {api_key[:10]}...")

# Try the citation lookup endpoint (more likely to have rate limits)
url = 'https://www.courtlistener.com/api/rest/v4/search/'

request = urllib.request.Request(url)
request.add_header('Authorization', f'Token {api_key}')

try:
    response = urllib.request.urlopen(request, timeout=10)
    print(f"Status: {response.status}")
    print(f"\nAll Headers:")
    for header, value in response.headers.items():
        print(f"  {header}: {value}")
        
    # Check for rate limit headers
    print(f"\nRate Limit Headers:")
    for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset',
                   'RateLimit-Limit', 'RateLimit-Remaining', 'RateLimit-Reset',
                   'X-Rate-Limit-Limit', 'X-Rate-Limit-Remaining', 'X-Rate-Limit-Reset']:
        value = response.headers.get(header)
        if value:
            print(f"  {header}: {value}")
            
except Exception as e:
    print(f"Error: {e}")
