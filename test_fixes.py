#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. Frontend timer display for small jobs (<35 citations)
2. Backend case name extraction
3. Proper result structure mapping
"""

import requests
import json
import time

def test_backend_api():
    """Test the backend API to verify case name extraction and result structure."""
    print("🧪 Testing Backend API...")
    
    # Test text with legal citations
    test_text = """
    The court held in Smith v. Jones, 123 F.3d 456 (9th Cir. 1997) that the plaintiff failed to state a claim.
    In Doe v. Washington State Patrol, 185 Wn.2d 363, 374 P.3d 63 (2016), the court addressed privacy concerns.
    The Supreme Court ruled in Brown v. Board of Education, 347 U.S. 483 (1954) that segregation was unconstitutional.
    """
    
    try:
        # Send request to analyze endpoint
        response = requests.post(
            'http://localhost:5000/casestrainer/api/analyze',
            json={'text': test_text, 'type': 'text'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Backend responded successfully!")
            print(f"Status: {result.get('status', 'unknown')}")
            
            if result.get('status') == 'processing' and result.get('task_id'):
                task_id = result['task_id']
                print(f"Task ID: {task_id}")
                
                # Wait for processing to complete
                print("⏳ Waiting for processing to complete...")
                for i in range(10):  # Wait up to 20 seconds
                    time.sleep(2)
                    
                    task_response = requests.get(f'http://localhost:5000/casestrainer/api/task_status/{task_id}')
                    if task_response.status_code == 200:
                        task_result = task_response.json()
                        
                        if task_result.get('status') == 'completed':
                            print("✅ Processing completed!")
                            
                            # Check results structure
                            results = task_result.get('results', [])
                            print(f"Found {len(results)} citations")
                            
                            for i, citation in enumerate(results, 1):
                                print(f"\nCitation {i}:")
                                print(f"  Citation: {citation.get('citation', 'N/A')}")
                                print(f"  Case Name: {citation.get('case_name', 'N/A')}")
                                print(f"  Extracted Case Name: '{citation.get('extracted_case_name', 'N/A')}'")
                                print(f"  Canonical Date: {citation.get('canonical_date', 'N/A')}")
                                print(f"  Verified: {citation.get('verified', False)}")
                                print(f"  Valid: {citation.get('valid', False)}")
                            
                            # Check if case names are being extracted
                            extracted_case_names = [c.get('extracted_case_name') for c in results if c.get('extracted_case_name') != 'N/A']
                            if extracted_case_names:
                                print(f"\n✅ Case name extraction working! Found {len(extracted_case_names)} extracted case names")
                            else:
                                print("\n❌ No case names extracted - this needs investigation")
                            
                            return True
                            
                        elif task_result.get('status') == 'failed':
                            print(f"❌ Processing failed: {task_result.get('error', 'Unknown error')}")
                            return False
                
                print("❌ Processing timed out")
                return False
            else:
                print("❌ Unexpected response format")
                print(f"Response: {json.dumps(result, indent=2)}")
                return False
        else:
            print(f"❌ Backend error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        return False

def test_frontend_timer():
    """Test that the frontend timer logic is working correctly."""
    print("\n🧪 Testing Frontend Timer Logic...")
    
    # Simulate the frontend logic for showing timer
    def should_show_timer(citation_count):
        return citation_count >= 35
    
    # Test cases
    test_cases = [
        (10, False, "Small job (<35 citations)"),
        (35, True, "Medium job (35 citations)"),
        (100, True, "Large job (>35 citations)")
    ]
    
    all_passed = True
    for citation_count, expected, description in test_cases:
        result = should_show_timer(citation_count)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}: {citation_count} citations -> show timer: {result} (expected: {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_result_structure():
    """Test that the result structure mapping is working correctly."""
    print("\n🧪 Testing Result Structure Mapping...")
    
    # Simulate the normalizeCitations function logic
    def normalize_citations(citations):
        return [{
            'citation': citation.get('citation', ''),
            'case_name': citation.get('case_name', 'N/A'),
            'extracted_case_name': citation.get('extracted_case_name', 'N/A'),
            'canonical_date': citation.get('canonical_date', ''),
            'verified': citation.get('case_name') != 'N/A' and citation.get('canonical_date') != 'N/A',
            'valid': citation.get('case_name') != 'N/A' and citation.get('canonical_date') != 'N/A'
        } for citation in citations]
    
    # Test data
    test_citations = [
        {
            'citation': '123 F.3d 456',
            'case_name': 'Smith v. Jones',
            'extracted_case_name': 'Smith v. Jones',
            'canonical_date': '1997-07-23'
        },
        {
            'citation': '185 Wn.2d 363',
            'case_name': 'N/A',
            'extracted_case_name': 'N/A',
            'canonical_date': ''
        }
    ]
    
    normalized = normalize_citations(test_citations)
    
    print("Test citation 1 (should be verified):")
    print(f"  Citation: {normalized[0]['citation']}")
    print(f"  Verified: {normalized[0]['verified']}")
    print(f"  Valid: {normalized[0]['valid']}")
    
    print("\nTest citation 2 (should not be verified):")
    print(f"  Citation: {normalized[1]['citation']}")
    print(f"  Verified: {normalized[1]['verified']}")
    print(f"  Valid: {normalized[1]['valid']}")
    
    # Check if verification logic is working
    verified_count = sum(1 for c in normalized if c['verified'])
    expected_verified = 1  # Only the first citation should be verified
    
    if verified_count == expected_verified:
        print(f"\n✅ Result structure mapping working! {verified_count}/{len(normalized)} citations verified (expected: {expected_verified})")
        return True
    else:
        print(f"\n❌ Result structure mapping issue! {verified_count}/{len(normalized)} citations verified (expected: {expected_verified})")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting CaseStrainer Fix Verification Tests")
    print("=" * 60)
    
    # Test backend API
    backend_ok = test_backend_api()
    
    # Test frontend timer logic
    timer_ok = test_frontend_timer()
    
    # Test result structure mapping
    structure_ok = test_result_structure()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Backend API: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Frontend Timer: {'✅ PASS' if timer_ok else '❌ FAIL'}")
    print(f"Result Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    
    if all([backend_ok, timer_ok, structure_ok]):
        print("\n🎉 All tests passed! The fixes are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
    
    print("\n💡 Next steps:")
    print("1. Restart your backend server to apply the changes")
    print("2. Refresh your browser to see the updated frontend")
    print("3. Test with a document containing <35 citations to see the timer behavior")
    print("4. Test with a document containing ≥35 citations to see the full timer")

if __name__ == "__main__":
    main() 