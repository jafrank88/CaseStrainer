#!/usr/bin/env python3
"""
Performance Comparison Test
Compare manual execution vs automated execution timing
"""

import time
import requests
import json
import sys

def test_simple_request():
    """Test a simple citation request to measure timing"""
    test_data = {
        "text": "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that...",
        "enable_verification": True
    }
    
    print("🔍 Performance Test")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Executable: {sys.executable}")
    print()
    
    # Test multiple times to get average
    times = []
    for i in range(3):
        print(f"Test {i+1}/3...")
        start_time = time.time()
        
        try:
            response = requests.post(
                "https://wolf.law.uw.edu/casestrainer/api/analyze",
                json=test_data,
                timeout=10
            )
            end_time = time.time()
            duration = end_time - start_time
            times.append(duration)
            
            print(f"  Status: {response.status_code}")
            print(f"  Duration: {duration:.3f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                processing_time = data.get('processing_time', 'unknown')
                print(f"  Server processing: {processing_time}")
            print()
            
        except Exception as e:
            print(f"  Error: {e}")
            print()
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print("📊 Results:")
        print(f"  Average time: {avg_time:.3f} seconds")
        print(f"  Min time: {min_time:.3f} seconds")
        print(f"  Max time: {max_time:.3f} seconds")
        print(f"  Variance: {max_time - min_time:.3f} seconds")
        
        # Compare with expected manual performance
        if avg_time < 1.0:
            print("✅ Performance is good (under 1 second)")
        elif avg_time < 2.0:
            print("⚠️  Performance is acceptable (1-2 seconds)")
        else:
            print("❌ Performance is slow (over 2 seconds)")
    
    print("\n💡 Manual execution should be faster due to:")
    print("  - Direct Python process (no Cursor overhead)")
    print("  - Native network requests")
    print("  - Optimized environment")

if __name__ == "__main__":
    test_simple_request() 