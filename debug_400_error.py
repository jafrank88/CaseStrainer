#!/usr/bin/env python3
"""
Debug script to identify the exact cause of 400 Bad Request error
This script tests the API endpoint directly to isolate the issue.
"""

import requests
import json
import os
import sys
from pathlib import Path

def test_api_endpoint_directly():
    """Test the API endpoint directly to identify the issue."""
    
    print("=== CaseStrainer API Debug - Direct Endpoint Test ===")
    print()
    
    # Test file path
    file_path = "1028814.pdf"
    
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File {file_path} not found")
        return False
    
    # API endpoint
    api_url = "https://wolf.law.uw.edu/casestrainer/api/analyze"
    
    print(f"📁 Testing file: {file_path}")
    print(f"🌐 API endpoint: {api_url}")
    print()
    
    try:
        # Prepare the file upload
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            
            print("📤 Sending request...")
            
            # Make the request
            response = requests.post(
                api_url,
                files=files,
                timeout=60,
                headers={
                    'User-Agent': 'CaseStrainer-Debug/1.0',
                    'Accept': 'application/json'
                }
            )
            
            print(f"📥 Response received:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Reason: {response.reason}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'Not specified')}")
            print(f"   Content-Length: {response.headers.get('Content-Length', 'Not specified')}")
            print()
            
            if response.status_code == 200:
                print("✅ SUCCESS: Request completed successfully!")
                try:
                    data = response.json()
                    print(f"📊 Response data keys: {list(data.keys())}")
                    if 'citations' in data:
                        print(f"📋 Citations found: {len(data['citations'])}")
                    elif 'status' in data:
                        print(f"📊 Status: {data['status']}")
                        if 'task_id' in data:
                            print(f"📋 Task ID: {data['task_id']}")
                except json.JSONDecodeError:
                    print("⚠️  Response is not valid JSON")
                    print(f"📄 Raw response: {response.text[:200]}...")
                return True
                
            elif response.status_code == 400:
                print("❌ 400 BAD REQUEST - Analyzing error details:")
                print()
                
                try:
                    error_data = response.json()
                    print("🔍 Error Response Details:")
                    print(f"   Error: {error_data.get('error', 'No error message')}")
                    print(f"   Message: {error_data.get('message', 'No message')}")
                    print(f"   Details: {error_data.get('details', 'No details')}")
                    print(f"   Status Code: {error_data.get('status_code', 'Not specified')}")
                    
                    # Check for specific validation errors
                    if 'validation_errors' in error_data:
                        print("   Validation Errors:")
                        for field, errors in error_data['validation_errors'].items():
                            print(f"     {field}: {errors}")
                    
                except json.JSONDecodeError:
                    print("🔍 Raw Error Response:")
                    print(f"   {response.text[:500]}...")
                
                return False
                
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
                
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERROR: Connection failed - {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_file_validation():
    """Test file validation rules."""
    
    print("=== File Validation Test ===")
    print()
    
    file_path = "1028814.pdf"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Get file info
    file_stat = os.stat(file_path)
    file_size = file_stat.st_size
    file_name = os.path.basename(file_path)
    
    print(f"📁 Filename: {file_name}")
    print(f"📏 File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    print()
    
    # Check file size limit (50MB)
    max_size = 50 * 1024 * 1024  # 50MB
    if file_size > max_size:
        print(f"❌ File too large: {file_size / (1024*1024):.2f} MB > 50 MB limit")
        return False
    else:
        print(f"✅ File size OK: {file_size / (1024*1024):.2f} MB < 50 MB limit")
    
    # Check file extension
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.html', '.htm']
    file_ext = Path(file_name).suffix.lower()
    
    if file_ext not in allowed_extensions:
        print(f"❌ Invalid file extension: {file_ext}")
        print(f"   Allowed: {allowed_extensions}")
        return False
    else:
        print(f"✅ File extension OK: {file_ext}")
    
    # Check filename for suspicious characters
    suspicious_chars = ['(', ')', '[', ']', '{', '}', '<', '>', '|', '\\', '/', ':', '*', '?', '"']
    has_suspicious = any(char in file_name for char in suspicious_chars)
    
    if has_suspicious:
        print(f"❌ Filename contains suspicious characters: {file_name}")
        return False
    else:
        print(f"✅ Filename OK: {file_name}")
    
    # Check if file is readable
    try:
        with open(file_path, 'rb') as f:
            header = f.read(10)
            if header.startswith(b'%PDF'):
                print("✅ File is a valid PDF")
            else:
                print(f"⚠️  File doesn't start with PDF header: {header}")
    except Exception as e:
        print(f"❌ Cannot read file: {e}")
        return False
    
    print()
    print("✅ All file validation checks passed!")
    return True

def test_network_connectivity():
    """Test network connectivity to the server."""
    
    print("=== Network Connectivity Test ===")
    print()
    
    base_url = "https://wolf.law.uw.edu"
    api_url = "https://wolf.law.uw.edu/casestrainer/api/health"
    
    try:
        print(f"🌐 Testing connection to: {base_url}")
        response = requests.get(base_url, timeout=10)
        print(f"✅ Base URL accessible: {response.status_code}")
        
        print(f"🌐 Testing API health endpoint: {api_url}")
        response = requests.get(api_url, timeout=10)
        print(f"✅ API health endpoint accessible: {response.status_code}")
        
        if response.status_code == 200:
            try:
                health_data = response.json()
                print(f"📊 Health status: {health_data.get('status', 'Unknown')}")
            except:
                print("📊 Health endpoint responded but not JSON")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Connection timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False

def main():
    """Main debugging function."""
    
    print("🔍 CaseStrainer 400 Error Debug Tool")
    print("=" * 50)
    print()
    
    # Test 1: Network connectivity
    print("1️⃣ Testing network connectivity...")
    if not test_network_connectivity():
        print("❌ Network connectivity failed - check your internet connection")
        return
    print()
    
    # Test 2: File validation
    print("2️⃣ Testing file validation...")
    if not test_file_validation():
        print("❌ File validation failed - check your file")
        return
    print()
    
    # Test 3: Direct API test
    print("3️⃣ Testing API endpoint directly...")
    success = test_api_endpoint_directly()
    
    print()
    print("=" * 50)
    if success:
        print("✅ All tests passed! The issue might be browser-specific.")
        print("💡 Try:")
        print("   - Different browser")
        print("   - Incognito/private mode")
        print("   - Clear browser cache")
    else:
        print("❌ API test failed - see details above")
        print("💡 The issue is likely server-side or configuration-related")

if __name__ == "__main__":
    main() 