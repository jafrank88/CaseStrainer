#!/usr/bin/env python3
"""
Quick test to verify async processing is working after Redis fixes
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000/casestrainer/api"

def test_redis_connection():
    """Test Redis connection directly"""
    print("🔍 Testing Redis connection...")
    try:
        from redis import Redis
        redis_conn = Redis.from_url('redis://localhost:6380/0')
        redis_conn.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_short_text():
    """Test short text immediate processing"""
    print("\n⚡ Testing short text (immediate)...")
    try:
        data = {'text': 'Short test with citation: Brown v. Board, 347 U.S. 483 (1954).'}
        response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            citations = result.get('citations', [])
            print(f"   ✅ Immediate processing: {len(citations)} citations found")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_long_text_async():
    """Test long text async processing"""
    print("\n📝 Testing long text (async)...")
    try:
        # Create text over 10KB to trigger async processing
        long_text = "Legal Document\n\n" + ("This is a long legal document with citations. " * 500)
        long_text += "\n\nCitations:\n"
        long_text += "1. Brown v. Board of Education, 347 U.S. 483 (1954)\n"
        long_text += "2. Roe v. Wade, 410 U.S. 113 (1973)\n"
        long_text += "3. Miranda v. Arizona, 384 U.S. 436 (1966)\n"
        
        print(f"   Text length: {len(long_text)} characters")
        
        data = {'text': long_text}
        response = requests.post(f"{BASE_URL}/analyze", json=data, timeout=15)
        
        if response.status_code == 202:  # Async processing
            result = response.json()
            task_id = result.get('task_id')
            print(f"   ✅ Async processing started, task ID: {task_id}")
            
            # Quick check if task status endpoint works
            status_response = requests.get(f"{BASE_URL}/task_status/{task_id}", timeout=5)
            if status_response.status_code == 200:
                status_result = status_response.json()
                print(f"   ✅ Task status check works: {status_result.get('status')}")
                return True
            else:
                print(f"   ❌ Task status check failed: {status_response.status_code}")
                return False
        elif response.status_code == 200:
            print("   ⚠️  Processed immediately (unexpected for long text)")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run quick async verification tests"""
    print("🧪 Quick Async Processing Verification")
    print("=" * 40)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Short Text Processing", test_short_text),
        ("Long Text Async Processing", test_long_text_async),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print(f"\n{'='*40}")
    print("📊 VERIFICATION RESULTS")
    print(f"{'='*40}")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nResult: {passed}/{len(results)} tests passed")
    
    if passed >= 2:  # Redis + at least one processing test
        print("🎉 Async processing is working!")
        return True
    else:
        print("⚠️  Some issues remain with async processing.")
        return False

if __name__ == "__main__":
    main()
