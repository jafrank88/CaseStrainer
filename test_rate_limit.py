"""Test script to check CourtListener API rate limiting status."""
import requests
import time
from datetime import datetime, timedelta
from src.config import COURTLISTENER_API_KEY

def check_rate_limit_status():
    """Check current rate limit status from CourtListener API."""
    url = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"
    headers = {
        'Authorization': f'Token {COURTLISTENER_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Test with a single citation
    payload = {"text": "87 Wn.2d 577"}
    
    print("=" * 60)
    print("Testing CourtListener API Rate Limit Status")
    print("=" * 60)
    print(f"API Key: {COURTLISTENER_API_KEY[:10]}...{COURTLISTENER_API_KEY[-5:]}")
    print(f"URL: {url}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print()
        
        # Check rate limit headers
        rate_limit_headers = {
            'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
            'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
            'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset'),
            'Retry-After': response.headers.get('Retry-After'),
        }
        
        print("Rate Limit Headers:")
        for header, value in rate_limit_headers.items():
            if value:
                print(f"  {header}: {value}")
            else:
                print(f"  {header}: Not provided")
        print()
        
        # Check if rate limited
        if response.status_code == 429:
            print("❌ RATE LIMITED (429)")
            retry_after = response.headers.get('Retry-After')
            reset_time = response.headers.get('X-RateLimit-Reset')
            
            if retry_after:
                try:
                    wait_seconds = float(retry_after)
                    reset_datetime = datetime.now() + timedelta(seconds=wait_seconds)
                    print(f"⏰ Retry-After: {wait_seconds} seconds")
                    print(f"⏰ Can retry at: {reset_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                except ValueError:
                    print(f"⏰ Retry-After: {retry_after} (could not parse)")
            
            if reset_time:
                try:
                    # Could be Unix timestamp or ISO format
                    if reset_time.isdigit():
                        reset_timestamp = int(reset_time)
                        reset_datetime = datetime.fromtimestamp(reset_timestamp)
                    else:
                        reset_datetime = datetime.fromisoformat(reset_time.replace('Z', '+00:00'))
                    print(f"⏰ X-RateLimit-Reset: {reset_time}")
                    print(f"⏰ Rate limit resets at: {reset_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
                except (ValueError, OSError):
                    print(f"⏰ X-RateLimit-Reset: {reset_time} (could not parse)")
            
            print()
            print("Response body:")
            print(response.text[:500])
            
        elif response.status_code == 200:
            print("✅ API is responding normally")
            if rate_limit_headers['X-RateLimit-Remaining']:
                remaining = int(rate_limit_headers['X-RateLimit-Remaining'])
                limit = int(rate_limit_headers['X-RateLimit-Limit']) if rate_limit_headers['X-RateLimit-Limit'] else 'unknown'
                print(f"📊 Remaining requests: {remaining}/{limit}")
                if remaining < 10:
                    print("⚠️  WARNING: Low remaining requests!")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
        
        print()
        print("All Response Headers:")
        for key, value in sorted(response.headers.items()):
            if 'rate' in key.lower() or 'retry' in key.lower() or 'limit' in key.lower():
                print(f"  {key}: {value}")
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_rate_limit_status()

