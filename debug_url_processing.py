#!/usr/bin/env python3
"""
Debug URL processing to understand the 400 error.
"""

import requests
import json

def debug_url_processing():
    """Debug URL processing with detailed error analysis."""
    
    # Test URL from the end-to-end test
    test_url = "https://www.courts.wa.gov/opinions/pdf/D2%2055297-8-II.pdf"
    
    print("🔗 Debugging URL Processing")
    print("=" * 60)
    print(f"📄 Test URL: {test_url}")
    print()
    
    # Test 1: Basic URL validation
    print("🧪 Test 1: URL Validation")
    try:
        # Try to access the URL directly
        head_response = requests.head(test_url, timeout=10)
        print(f"  URL HEAD request: {head_response.status_code}")
        print(f"  Content-Type: {head_response.headers.get('Content-Type', 'N/A')}")
        print(f"  Content-Length: {head_response.headers.get('Content-Length', 'N/A')}")
    except Exception as e:
        print(f"  ❌ URL HEAD request failed: {e}")
    
    # Test 2: API URL processing
    print(f"\n🧪 Test 2: API URL Processing")
    try:
        print("📤 Submitting URL to API...")
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"url": test_url},
            timeout=60,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 400:
            print("❌ 400 Bad Request - analyzing error...")
            try:
                error_data = response.json()
                print(f"  Error response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"  Raw error response: {response.text}")
        elif response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response keys: {list(data.keys())}")
            print(f"  Success: {data.get('success')}")
            print(f"  Message: {data.get('message')}")
            print(f"  Citations: {len(data.get('citations', []))}")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"  Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"💥 API request failed: {e}")
    
    # Test 3: Try different URL formats
    print(f"\n🧪 Test 3: Testing Different URL Formats")
    
    test_urls = [
        "https://www.courts.wa.gov/opinions/pdf/D2%2055297-8-II.pdf",  # Original
        "https://www.courts.wa.gov/opinions/pdf/D2 55297-8-II.pdf",   # Unescaped
        "https://httpbin.org/json",  # Simple JSON endpoint for testing
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"  Test URL {i}: {url}")
        try:
            response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json={"url": url},
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            print(f"    Status: {response.status_code}")
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    print(f"    Error: {error_data.get('error', 'No error message')}")
                except:
                    print(f"    Raw error: {response.text[:100]}...")
            elif response.status_code == 200:
                data = response.json()
                print(f"    Success: {data.get('success')}")
                print(f"    Message: {data.get('message', 'No message')}")
        except Exception as e:
            print(f"    Exception: {e}")

def test_url_processing_directly():
    """Test URL processing using the unified input processor directly."""
    
    print(f"\n🔧 Testing URL Processing Directly")
    print("=" * 60)
    
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        
        from src.unified_input_processor import process_url_input
        import uuid
        
        test_url = "https://httpbin.org/json"  # Simple test URL
        request_id = str(uuid.uuid4())
        
        print(f"📄 Test URL: {test_url}")
        print(f"🆔 Request ID: {request_id}")
        
        result = process_url_input(test_url, request_id)
        
        print(f"📊 Direct processing result:")
        print(f"  Success: {result.get('success')}")
        print(f"  Error: {result.get('error', 'None')}")
        print(f"  Citations: {len(result.get('citations', []))}")
        print(f"  Processing mode: {result.get('metadata', {}).get('processing_mode')}")
        
        if not result.get('success'):
            print(f"  Error details: {result.get('error')}")
            
    except Exception as e:
        print(f"💥 Direct URL processing failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run URL processing debug."""
    debug_url_processing()
    test_url_processing_directly()

if __name__ == "__main__":
    main()
