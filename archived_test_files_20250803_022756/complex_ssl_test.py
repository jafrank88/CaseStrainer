#!/usr/bin/env python3
"""
Complex SSL/HTTPS Test for Production Server
Tests various connection methods and SSL configurations
"""

import requests
import urllib3
import ssl
import time
import json
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for testing
urllib3.disable_warnings(InsecureRequestWarning)

def test_connection_methods():
    """Test different connection methods to diagnose SSL issues"""
    
    base_urls = [
        "https://wolf.law.uw.edu/casestrainer/api",
        "http://wolf.law.uw.edu/casestrainer/api",  # Try HTTP fallback
        "https://wolf.law.uw.edu/casestrainer/api/health",
        "http://wolf.law.uw.edu/casestrainer/api/health"
    ]
    
    test_data = {
        "text": "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that...",
        "enable_verification": True
    }
    
    print("🔍 Complex SSL/HTTPS Test")
    print("=" * 60)
    
    for i, url in enumerate(base_urls, 1):
        print(f"\n{i}. Testing: {url}")
        print("-" * 40)
        
        # Test 1: Basic GET request
        try:
            print("   GET request...")
            start_time = time.time()
            response = requests.get(url, timeout=10, verify=False)
            duration = time.time() - start_time
            
            print(f"   Status: {response.status_code}")
            print(f"   Time: {duration:.3f}s")
            print(f"   Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Success! Data: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"   ⚠️  Non-JSON response: {response.text[:100]}...")
            else:
                print(f"   ❌ Error: {response.text[:100]}...")
                
        except requests.exceptions.SSLError as e:
            print(f"   🔒 SSL Error: {e}")
        except requests.exceptions.ConnectionError as e:
            print(f"   🔌 Connection Error: {e}")
        except requests.exceptions.Timeout as e:
            print(f"   ⏰ Timeout: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected Error: {e}")
        
        # Test 2: POST request (if it's an analyze endpoint)
        if "analyze" in url or url.endswith("/api"):
            try:
                print("   POST request...")
                start_time = time.time()
                response = requests.post(url, json=test_data, timeout=10, verify=False)
                duration = time.time() - start_time
                
                print(f"   Status: {response.status_code}")
                print(f"   Time: {duration:.3f}s")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        citations = data.get('citations', [])
                        print(f"   ✅ Success! Found {len(citations)} citations")
                        if citations:
                            citation = citations[0]
                            print(f"   Citation: {citation.get('citation', 'N/A')}")
                            print(f"   Case: {citation.get('case_name', 'N/A')}")
                            print(f"   Date: {citation.get('extracted_date', 'N/A')}")
                    except:
                        print(f"   ⚠️  Non-JSON response: {response.text[:100]}...")
                else:
                    print(f"   ❌ Error: {response.text[:100]}...")
                    
            except requests.exceptions.SSLError as e:
                print(f"   🔒 SSL Error: {e}")
            except requests.exceptions.ConnectionError as e:
                print(f"   🔌 Connection Error: {e}")
            except requests.exceptions.Timeout as e:
                print(f"   ⏰ Timeout: {e}")
            except Exception as e:
                print(f"   ❌ Unexpected Error: {e}")

def test_ssl_configuration():
    """Test SSL configuration and certificates"""
    
    print("\n🔒 SSL Configuration Test")
    print("=" * 40)
    
    try:
        import socket
        import ssl
        
        hostname = "wolf.law.uw.edu"
        port = 443
        
        print(f"Testing SSL connection to {hostname}:{port}")
        
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"✅ SSL connection successful")
                print(f"   Protocol: {ssock.version()}")
                print(f"   Cipher: {ssock.cipher()}")
                print(f"   Certificate: {ssock.getpeercert()}")
                
    except Exception as e:
        print(f"❌ SSL test failed: {e}")

def test_production_endpoints():
    """Test specific production endpoints"""
    
    print("\n🏭 Production Endpoints Test")
    print("=" * 40)
    
    endpoints = [
        ("Health Check", "https://wolf.law.uw.edu/casestrainer/api/health"),
        ("Analyze", "https://wolf.law.uw.edu/casestrainer/api/analyze"),
        ("Version", "https://wolf.law.uw.edu/casestrainer/api/version")
    ]
    
    test_data = {
        "text": "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that...",
        "enable_verification": True
    }
    
    for name, url in endpoints:
        print(f"\nTesting {name}: {url}")
        
        try:
            if "analyze" in url:
                response = requests.post(url, json=test_data, timeout=10, verify=False)
            else:
                response = requests.get(url, timeout=10, verify=False)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ Success: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"   ⚠️  Non-JSON: {response.text[:100]}...")
            else:
                print(f"   ❌ Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    test_connection_methods()
    test_ssl_configuration()
    test_production_endpoints()
    
    print("\n" + "=" * 60)
    print("🎯 Test Complete!")
    print("\n💡 Based on the results:")
    print("   - If SSL errors occur, the server may need SSL configuration")
    print("   - If HTTP works but HTTPS doesn't, it's an SSL setup issue")
    print("   - If both fail, it's a network/connectivity issue") 