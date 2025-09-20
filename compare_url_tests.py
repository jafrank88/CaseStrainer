#!/usr/bin/env python3
"""
Compare URL processing between individual test and end-to-end test to identify differences.
"""

import requests
import json

def test_individual_url():
    """Test URL processing the same way as test_new_url.py"""
    
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    print("🧪 Individual URL Test (test_new_url.py style)")
    print("=" * 60)
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",
            json={"url": test_url},
            timeout=60
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Success: {data.get('success')}")
            print(f"  Citations: {len(data.get('citations', []))}")
            print(f"  Message: {data.get('message')}")
            print(f"  Has task_id: {'task_id' in data}")
            print(f"  Processing mode: {data.get('metadata', {}).get('processing_mode', 'N/A')}")
            
            # Show response structure
            print(f"  Response keys: {list(data.keys())}")
            
            return data
        else:
            print(f"  Failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  Exception: {e}")
        return None

def test_end_to_end_url():
    """Test URL processing the same way as end-to-end test"""
    
    test_url = "https://www.courts.wa.gov/opinions/pdf/1033940.pdf"
    
    print("\n🧪 End-to-End URL Test (test_end_to_end_complete.py style)")
    print("=" * 60)
    
    try:
        response = requests.post(
            "http://localhost:8080/casestrainer/api/analyze",  # Same URL as individual test
            json={"url": test_url},
            timeout=60
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"  ❌ URL request failed with status {response.status_code}")
            return None
            
        data = response.json()
        
        # Handle both sync and async responses (end-to-end logic)
        if data.get('task_id'):
            print("  🔄 URL processing queued for async")
            print("  End-to-end test would consider this SUCCESS")
            return data
        else:
            citations = data.get('citations', [])
            if len(citations) > 0:
                print(f"  ✅ URL processing working: {len(citations)} citations found")
                print("  End-to-end test would consider this SUCCESS")
                return data
            else:
                print("  ⚠️ URL processing completed but no citations found")
                print("  End-to-end test would consider this SUCCESS (not necessarily a failure)")
                return data
                
    except Exception as e:
        print(f"  ❌ URL processing test failed: {e}")
        return None

def analyze_differences(individual_result, end_to_end_result):
    """Analyze the differences between the two test results."""
    
    print("\n🔍 Analysis of Differences")
    print("=" * 60)
    
    if individual_result is None and end_to_end_result is None:
        print("  Both tests failed - same result")
        return
    
    if individual_result is None:
        print("  Individual test failed, end-to-end succeeded - different results!")
        return
        
    if end_to_end_result is None:
        print("  End-to-end test failed, individual succeeded - different results!")
        return
    
    # Compare key metrics
    individual_citations = len(individual_result.get('citations', []))
    end_to_end_citations = len(end_to_end_result.get('citations', []))
    
    individual_success = individual_result.get('success')
    end_to_end_success = end_to_end_result.get('success')
    
    individual_task_id = 'task_id' in individual_result
    end_to_end_task_id = 'task_id' in end_to_end_result
    
    print(f"  Citations found:")
    print(f"    Individual: {individual_citations}")
    print(f"    End-to-end: {end_to_end_citations}")
    print(f"    Same? {'✅' if individual_citations == end_to_end_citations else '❌'}")
    
    print(f"  Success status:")
    print(f"    Individual: {individual_success}")
    print(f"    End-to-end: {end_to_end_success}")
    print(f"    Same? {'✅' if individual_success == end_to_end_success else '❌'}")
    
    print(f"  Has task_id:")
    print(f"    Individual: {individual_task_id}")
    print(f"    End-to-end: {end_to_end_task_id}")
    print(f"    Same? {'✅' if individual_task_id == end_to_end_task_id else '❌'}")
    
    # Check if the responses are identical
    if individual_result == end_to_end_result:
        print("\n  🎉 IDENTICAL RESPONSES - Tests should behave the same!")
    else:
        print("\n  ⚠️ DIFFERENT RESPONSES - This explains the different behavior")
        
        # Show key differences
        individual_keys = set(individual_result.keys())
        end_to_end_keys = set(end_to_end_result.keys())
        
        if individual_keys != end_to_end_keys:
            print(f"    Different keys:")
            print(f"      Individual only: {individual_keys - end_to_end_keys}")
            print(f"      End-to-end only: {end_to_end_keys - individual_keys}")

def check_end_to_end_test_logic():
    """Check what the end-to-end test actually considers success/failure."""
    
    print("\n📋 End-to-End Test Success Criteria")
    print("=" * 60)
    
    print("  The end-to-end test considers URL processing successful if:")
    print("    1. HTTP status is 200, AND")
    print("    2. Either:")
    print("       a) Has task_id (async processing queued), OR")
    print("       b) Has citations > 0, OR")
    print("       c) Has citations = 0 (still considered success)")
    print()
    print("  The end-to-end test only fails if:")
    print("    1. HTTP status != 200, OR")
    print("    2. Exception occurs")
    print()
    print("  🔍 This means the URL test is probably PASSING but being")
    print("     reported as failing due to a different issue!")

def main():
    """Run comparison tests."""
    
    print("🔍 Comparing URL Test Behaviors")
    print("=" * 60)
    
    # Run both tests
    individual_result = test_individual_url()
    end_to_end_result = test_end_to_end_url()
    
    # Analyze differences
    analyze_differences(individual_result, end_to_end_result)
    
    # Check test logic
    check_end_to_end_test_logic()

if __name__ == "__main__":
    main()
