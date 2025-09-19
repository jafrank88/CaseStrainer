#!/usr/bin/env python3
"""
Test the improved error handling for URL and file processing.
"""

import requests
import json

def test_improved_error_handling():
    """Test various error scenarios to verify improved error messages."""
    
    print("🧪 Testing Improved Error Handling")
    print("=" * 60)
    
    # Test cases for different error scenarios
    test_cases = [
        {
            'name': 'Valid URL',
            'data': {'url': 'https://www.courts.wa.gov/opinions/pdf/1033940.pdf'},
            'expected_status': 200,
            'description': 'Should work correctly'
        },
        {
            'name': 'Invalid URL - No Protocol',
            'data': {'url': 'www.example.com'},
            'expected_status': 400,
            'description': 'Should show protocol error'
        },
        {
            'name': 'Invalid URL - Empty',
            'data': {'url': ''},
            'expected_status': 400,
            'description': 'Should show empty URL error'
        },
        {
            'name': 'Invalid URL - Not a String',
            'data': {'url': 123},
            'expected_status': 400,
            'description': 'Should show invalid URL type error'
        },
        {
            'name': 'Non-existent URL',
            'data': {'url': 'https://this-domain-does-not-exist-12345.com/file.pdf'},
            'expected_status': 400,
            'description': 'Should show connection error'
        },
        {
            'name': '404 URL',
            'data': {'url': 'https://httpbin.org/status/404'},
            'expected_status': 400,
            'description': 'Should show 404 error'
        },
        {
            'name': '403 URL',
            'data': {'url': 'https://httpbin.org/status/403'},
            'expected_status': 400,
            'description': 'Should show forbidden error'
        },
        {
            'name': '500 URL',
            'data': {'url': 'https://httpbin.org/status/500'},
            'expected_status': 400,
            'description': 'Should show server error'
        },
        {
            'name': 'Valid Text',
            'data': {'text': 'This is a test document with State v. Johnson, 160 Wn.2d 500.'},
            'expected_status': 200,
            'description': 'Should work correctly'
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print(f"   Description: {test_case['description']}")
        
        try:
            response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json=test_case['data'],
                timeout=30
            )
            
            actual_status = response.status_code
            expected_status = test_case['expected_status']
            
            print(f"   Status: {actual_status} (expected: {expected_status})")
            
            if actual_status == expected_status:
                print("   ✅ Status matches expectation")
                status_result = "✅ PASS"
            else:
                print("   ❌ Status doesn't match expectation")
                status_result = "❌ FAIL"
            
            # Check error message quality for 400 responses
            if actual_status == 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', 'No error message')
                    print(f"   Error message: {error_message}")
                    
                    # Check if error message is user-friendly (not technical)
                    if any(word in error_message.lower() for word in ['please', 'check', 'try', 'provide']):
                        print("   ✅ Error message is user-friendly")
                        message_result = "✅ GOOD"
                    else:
                        print("   ⚠️ Error message could be more user-friendly")
                        message_result = "⚠️ OK"
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Could not parse error response: {response.text[:100]}...")
                    message_result = "❌ BAD"
            else:
                message_result = "N/A"
            
            # Check success cases
            if actual_status == 200:
                try:
                    data = response.json()
                    success = data.get('success', False)
                    citations = len(data.get('citations', []))
                    print(f"   Success: {success}, Citations: {citations}")
                    message_result = "✅ GOOD"
                except:
                    print("   ❌ Could not parse success response")
                    message_result = "❌ BAD"
            
            results.append({
                'test': test_case['name'],
                'status': status_result,
                'message': message_result
            })
            
        except Exception as e:
            print(f"   💥 Test failed with exception: {e}")
            results.append({
                'test': test_case['name'],
                'status': "❌ EXCEPTION",
                'message': "❌ EXCEPTION"
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 ERROR HANDLING TEST SUMMARY")
    print("=" * 60)
    
    for result in results:
        print(f"{result['status']} {result['test']} - Message: {result['message']}")
    
    # Overall assessment
    passed_tests = sum(1 for r in results if r['status'] == "✅ PASS")
    good_messages = sum(1 for r in results if r['message'] == "✅ GOOD")
    total_tests = len(results)
    
    print(f"\nOverall Results:")
    print(f"  Status Tests: {passed_tests}/{total_tests} passed")
    print(f"  Message Quality: {good_messages} good messages")
    
    if passed_tests == total_tests and good_messages >= total_tests - 2:  # Allow some N/A
        print("🎉 ERROR HANDLING IS WORKING WELL!")
    else:
        print("⚠️ Error handling needs improvement")

def main():
    """Run error handling tests."""
    test_improved_error_handling()

if __name__ == "__main__":
    main()
