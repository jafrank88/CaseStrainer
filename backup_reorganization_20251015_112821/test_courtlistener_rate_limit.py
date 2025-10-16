"""
Test CourtListener API rate limit status.
Tests a simple citation lookup and reports rate limit information.
"""

import requests
import json
from datetime import datetime
import os
import sys
from pathlib import Path

# Add src to path for config
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from config import COURTLISTENER_API_KEY
except:
    COURTLISTENER_API_KEY = os.getenv('COURTLISTENER_API_KEY', '')

def test_rate_limit():
    """Test CourtListener API and check rate limit status."""
    
    print("=" * 80)
    print(f"COURTLISTENER API RATE LIMIT TEST")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    if not COURTLISTENER_API_KEY:
        print("\n❌ ERROR: No API key found!")
        print("Set COURTLISTENER_API_KEY environment variable or check .env file")
        return False
    
    print(f"\n✓ API Key found: {COURTLISTENER_API_KEY[:10]}...{COURTLISTENER_API_KEY[-10:]}")
    
    # Test with a simple citation lookup
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        "Authorization": f"Token {COURTLISTENER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    test_citation = "617 B.R. 636"
    data = {"citation": test_citation}
    
    print(f"\nTesting citation lookup: {test_citation}")
    print(f"Endpoint: {url}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        print(f"\n{'='*80}")
        print(f"RESPONSE STATUS: {response.status_code}")
        print(f"{'='*80}")
        
        # Check rate limit headers
        print("\nRate Limit Information:")
        rate_limit_headers = {
            'X-RateLimit-Limit': 'Total requests allowed',
            'X-RateLimit-Remaining': 'Requests remaining',
            'X-RateLimit-Reset': 'Time when limit resets (Unix timestamp)',
            'Retry-After': 'Seconds to wait before retrying'
        }
        
        found_rate_info = False
        for header, description in rate_limit_headers.items():
            value = response.headers.get(header)
            if value:
                found_rate_info = True
                print(f"  {header}: {value} ({description})")
                
                # Convert reset time if available
                if header == 'X-RateLimit-Reset' and value:
                    try:
                        reset_time = datetime.fromtimestamp(int(value))
                        print(f"    → Resets at: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    except:
                        pass
        
        if not found_rate_info:
            print("  (No rate limit headers found in response)")
        
        # Check response content
        print("\nResponse Details:")
        if response.status_code == 200:
            print("  ✓ SUCCESS - API is working!")
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    print(f"  Found {len(data)} result(s)")
                    if 'caseName' in data[0]:
                        print(f"  Case: {data[0].get('caseName', 'N/A')}")
                else:
                    print("  No results found for citation")
            except:
                print(f"  Response text: {response.text[:200]}")
                
        elif response.status_code == 429:
            print("  ❌ RATE LIMITED - Too many requests!")
            print(f"  Message: {response.text[:200]}")
            retry_after = response.headers.get('Retry-After', 'Unknown')
            print(f"\n  Wait {retry_after} seconds before next request")
            
        elif response.status_code == 401:
            print("  ❌ UNAUTHORIZED - API key invalid or expired")
            
        elif response.status_code == 403:
            print("  ❌ FORBIDDEN - Access denied")
            
        elif response.status_code == 404:
            print("  ⚠ Citation not found (but API is working)")
            
        else:
            print(f"  ⚠ Unexpected status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
        
        print("\n" + "=" * 80)
        
        # Return True if we can make requests (not rate limited)
        return response.status_code != 429
        
    except requests.exceptions.Timeout:
        print("\n❌ ERROR: Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ ERROR: {e}")
        return False

def main():
    success = test_rate_limit()
    
    if success:
        print("\n✓ CourtListener API is accessible")
        print("\nTo test every 10 minutes, run:")
        print("  while ($true) { python test_courtlistener_rate_limit.py; Start-Sleep -Seconds 600 }")
    else:
        print("\n✗ CourtListener API access failed or rate limited")
        print("\nCheck again in 10 minutes:")
        print("  Start-Sleep -Seconds 600; python test_courtlistener_rate_limit.py")

if __name__ == '__main__':
    main()
