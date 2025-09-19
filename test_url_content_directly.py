#!/usr/bin/env python3
"""
Test URL content fetching directly to understand the issue.
"""

import requests

def test_url_content():
    """Test fetching URL content directly."""
    
    test_url = "https://www.courts.wa.gov/opinions/pdf/D2%2055297-8-II.pdf"
    
    print("🔗 Testing URL Content Fetching")
    print("=" * 60)
    print(f"📄 URL: {test_url}")
    print()
    
    try:
        print("📤 Making direct request...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(test_url, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"📊 Content-Length: {response.headers.get('content-length', 'N/A')}")
        print(f"📊 Response Size: {len(response.content)} bytes")
        
        # Check if it's actually HTML (error page)
        content_type = response.headers.get('content-type', '').lower()
        if 'html' in content_type:
            print("\n⚠️ Server returned HTML instead of PDF")
            print("📄 HTML content preview:")
            print(response.text[:500])
            print("...")
            
            # Check if it's a redirect or error page
            if "404" in response.text or "not found" in response.text.lower():
                print("❌ This appears to be a 404 error page")
            elif "redirect" in response.text.lower() or "moved" in response.text.lower():
                print("⚠️ This appears to be a redirect page")
            else:
                print("🔍 Unknown HTML response")
        elif 'pdf' in content_type:
            print("✅ Successfully received PDF content")
            print(f"📄 PDF size: {len(response.content)} bytes")
        else:
            print(f"⚠️ Unexpected content type: {content_type}")
            
    except Exception as e:
        print(f"💥 Request failed: {e}")

def test_alternative_urls():
    """Test with some alternative URLs that should work."""
    
    print("\n🧪 Testing Alternative URLs")
    print("=" * 60)
    
    # Test URLs that should work
    test_urls = [
        "https://httpbin.org/json",  # Simple JSON
        "https://httpbin.org/html",  # Simple HTML
        "https://www.example.com",   # Basic website
    ]
    
    for url in test_urls:
        print(f"\n📄 Testing: {url}")
        try:
            response = requests.get(url, timeout=10)
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"  Size: {len(response.content)} bytes")
            
            # Test with our API
            print("  Testing with API...")
            api_response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json={"url": url},
                timeout=30
            )
            print(f"  API Status: {api_response.status_code}")
            if api_response.status_code == 400:
                try:
                    error_data = api_response.json()
                    print(f"  API Error: {error_data.get('error', 'No error message')}")
                except:
                    print(f"  API Raw Error: {api_response.text[:100]}...")
            elif api_response.status_code == 200:
                data = api_response.json()
                print(f"  API Success: {data.get('success')}")
                print(f"  API Citations: {len(data.get('citations', []))}")
                
        except Exception as e:
            print(f"  ❌ Failed: {e}")

def main():
    """Run URL content tests."""
    test_url_content()
    test_alternative_urls()

if __name__ == "__main__":
    main()
