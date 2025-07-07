#!/usr/bin/env python3
import requests
import json
import time

def test_simple_endpoint():
    """Test if the basic endpoint responds"""
    print("=== TESTING BASIC ENDPOINT ===")
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        print(f"✅ Root endpoint responds - Status: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_analyze_endpoint():
    """Test the analyze endpoint with a simple text request"""
    print("\n=== TESTING ANALYZE ENDPOINT ===")
    
    test_data = {
        "text": "Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982)",
        "type": "text"
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json=test_data,
            timeout=30
        )
        
        print(f"✅ Analyze endpoint responds - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ Analyze endpoint failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Analyze endpoint error: {e}")
        return None

def test_file_upload_simple():
    """Test file upload with a simple approach"""
    print("\n=== TESTING FILE UPLOAD (SIMPLE) ===")
    
    # Create a simple text file for testing
    test_file_content = "This is a test document with citation: Seattle Times Co. v. Ishikawa, 97 Wn.2d 30, 640 P.2d 716 (1982)"
    
    try:
        # Simulate file upload with text content
        files = {'file': ('test.txt', test_file_content, 'text/plain')}
        
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            files=files,
            timeout=30
        )
        
        print(f"✅ File upload responds - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ File upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ File upload error: {e}")
        return None

def test_url_upload_simple():
    """Test URL upload with a simple approach"""
    print("\n=== TESTING URL UPLOAD (SIMPLE) ===")
    
    test_data = {
        "url": "https://example.com/test.pdf",
        "type": "url"
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/casestrainer/api/analyze",
            json=test_data,
            timeout=30
        )
        
        print(f"✅ URL upload responds - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"❌ URL upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ URL upload error: {e}")
        return None

def main():
    """Main test function"""
    print("🔍 SIMPLE FRONTEND METHODS TEST")
    print("=" * 40)
    
    # Test basic connectivity
    if not test_simple_endpoint():
        print("\n❌ Cannot reach server - check if it's running")
        return
    
    # Test each method
    methods = [
        ("Text Analysis", test_analyze_endpoint),
        ("File Upload", test_file_upload_simple),
        ("URL Upload", test_url_upload_simple)
    ]
    
    results = {}
    
    for method_name, test_func in methods:
        try:
            result = test_func()
            results[method_name] = result is not None
            if result:
                print(f"✅ {method_name}: SUCCESS")
            else:
                print(f"❌ {method_name}: FAILED")
        except Exception as e:
            print(f"❌ {method_name}: ERROR - {e}")
            results[method_name] = False
    
    # Summary
    print("\n" + "=" * 40)
    print("📋 TEST SUMMARY")
    print("=" * 40)
    
    for method_name, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"{method_name}: {status}")
    
    working_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nOverall: {working_count}/{total_count} methods working")
    
    if working_count == 0:
        print("\n💡 All methods are failing - check backend server")
    elif working_count == total_count:
        print("\n🎉 All methods are working correctly!")
    else:
        print("\n⚠️ Some methods need attention")

if __name__ == "__main__":
    main() 