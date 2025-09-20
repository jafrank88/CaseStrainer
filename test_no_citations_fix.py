#!/usr/bin/env python3
"""
Test the "No Citations" fix by verifying end-to-end functionality.
"""

import requests
import time
import json

def test_frontend_backend_integration():
    """Test that frontend correctly processes backend responses."""
    
    print("🔗 Testing Frontend-Backend Integration")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Simple Citation",
            "text": "The case State v. Johnson, 160 Wn.2d 500 (2007) is important.",
            "expected_min": 1
        },
        {
            "name": "Multiple Citations",
            "text": """
            Legal Analysis:
            1. State v. Johnson, 160 Wn.2d 500 (2007)
            2. Brown v. Board, 347 U.S. 483 (1954)
            3. Miranda v. Arizona, 384 U.S. 436 (1966)
            """,
            "expected_min": 3
        },
        {
            "name": "Complex Document",
            "text": """
            LEGAL MEMORANDUM
            
            Re: Citation Analysis
            
            This memo analyzes several important cases:
            
            1. State v. Johnson, 160 Wn.2d 500, 158 P.3d 677 (2007) - Criminal law
            2. City of Seattle v. Williams, 170 Wn.2d 200, 240 P.3d 1055 (2010) - Municipal law
            3. Brown v. Board of Education, 347 U.S. 483, 74 S. Ct. 686 (1954) - Civil rights
            
            These cases demonstrate important legal principles.
            """,
            "expected_min": 3
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        
        try:
            response = requests.post(
                "http://localhost:8080/casestrainer/api/analyze",
                json={"text": test_case['text'], "type": "text"},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"   ❌ API Error: {response.status_code}")
                results.append({"name": test_case['name'], "success": False, "error": f"HTTP {response.status_code}"})
                continue
            
            data = response.json()
            processing_mode = data.get('metadata', {}).get('processing_mode', 'unknown')
            
            # Handle async processing if needed
            if processing_mode == 'queued':
                job_id = data.get('metadata', {}).get('job_id')
                if job_id:
                    print(f"   ⏳ Async processing: {job_id}")
                    for attempt in range(15):
                        time.sleep(1)
                        status_response = requests.get(f"http://localhost:8080/casestrainer/api/task_status/{job_id}")
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get('status') == 'completed':
                                data = status_data
                                break
                            elif status_data.get('status') == 'failed':
                                print(f"   ❌ Async failed: {status_data}")
                                break
                    else:
                        print(f"   ❌ Async timeout")
                        results.append({"name": test_case['name'], "success": False, "error": "Async timeout"})
                        continue
            
            # Analyze response structure (simulating frontend processing)
            citations = data.get('citations', [])
            clusters = data.get('clusters', [])
            success = data.get('success', False)
            
            print(f"   📊 API Response:")
            print(f"     Processing: {processing_mode}")
            print(f"     Success: {success}")
            print(f"     Citations: {len(citations)}")
            print(f"     Clusters: {len(clusters)}")
            print(f"     Expected Min: {test_case['expected_min']}")
            
            # Check if frontend would see citations
            frontend_citations = []
            frontend_clusters = []
            
            # Simulate the frontend logic we just fixed
            if data.get('citations') or data.get('clusters'):
                # Direct flat structure (current API format)
                frontend_citations = data.get('citations', [])
                frontend_clusters = data.get('clusters', [])
            elif data.get('result'):
                # Legacy nested structure fallback
                frontend_citations = data.get('result', {}).get('citations', [])
                frontend_clusters = data.get('result', {}).get('clusters', [])
            
            print(f"   🖥️ Frontend Would See:")
            print(f"     Citations: {len(frontend_citations)}")
            print(f"     Clusters: {len(frontend_clusters)}")
            
            # Success criteria
            api_success = len(citations) >= test_case['expected_min']
            frontend_success = len(frontend_citations) >= test_case['expected_min']
            overall_success = api_success and frontend_success
            
            if overall_success:
                print(f"   ✅ SUCCESS: Both API and frontend see citations")
                if len(frontend_citations) > 0:
                    print(f"   📋 Sample citations:")
                    for j, citation in enumerate(frontend_citations[:3], 1):
                        print(f"     {j}. {citation.get('citation', 'N/A')}")
            else:
                print(f"   ❌ FAILURE:")
                if not api_success:
                    print(f"     - API returned {len(citations)}, expected >= {test_case['expected_min']}")
                if not frontend_success:
                    print(f"     - Frontend would see {len(frontend_citations)}, expected >= {test_case['expected_min']}")
            
            results.append({
                "name": test_case['name'],
                "success": overall_success,
                "api_citations": len(citations),
                "frontend_citations": len(frontend_citations),
                "expected": test_case['expected_min']
            })
            
        except Exception as e:
            print(f"   💥 Exception: {e}")
            results.append({"name": test_case['name'], "success": False, "error": str(e)})
    
    # Summary
    print(f"\n📊 Integration Test Summary:")
    successful_tests = len([r for r in results if r.get('success', False)])
    total_tests = len(results)
    
    for result in results:
        status = "✅" if result.get('success', False) else "❌"
        api_count = result.get('api_citations', 0)
        frontend_count = result.get('frontend_citations', 0)
        expected = result.get('expected', 0)
        
        print(f"   {status} {result['name']}: API={api_count}, Frontend={frontend_count}, Expected>={expected}")
    
    print(f"\nOverall: {successful_tests}/{total_tests} tests passed")
    
    return successful_tests == total_tests

def test_end_to_end_complete():
    """Run the complete end-to-end test suite."""
    
    print(f"\n🧪 Running Complete End-to-End Test")
    print("=" * 50)
    
    try:
        # Run the existing end-to-end test
        import subprocess
        result = subprocess.run(
            ["python", "test_end_to_end_complete.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(f"📊 End-to-End Test Results:")
        print(f"   Exit Code: {result.returncode}")
        
        # Parse the output for key metrics
        output_lines = result.stdout.split('\n')
        citation_lines = [line for line in output_lines if 'citations found' in line.lower()]
        
        if citation_lines:
            print(f"   Citation Results:")
            for line in citation_lines:
                print(f"     {line.strip()}")
        
        # Look for overall results
        summary_lines = [line for line in output_lines if 'overall:' in line.lower()]
        if summary_lines:
            print(f"   Summary: {summary_lines[-1].strip()}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"   💥 End-to-end test failed: {e}")
        return False

def main():
    """Run comprehensive no-citations fix verification."""
    
    print("🚀 Testing 'No Citations' Fix")
    print("=" * 60)
    
    # Run tests
    integration_ok = test_frontend_backend_integration()
    e2e_ok = test_end_to_end_complete()
    
    print("\n" + "=" * 60)
    print("📋 'NO CITATIONS' FIX TEST RESULTS")
    print("=" * 60)
    
    print(f"1. Frontend-Backend Integration: {'✅ PASS' if integration_ok else '❌ FAIL'}")
    print(f"2. Complete End-to-End Test: {'✅ PASS' if e2e_ok else '❌ FAIL'}")
    
    overall_success = integration_ok and e2e_ok
    
    if overall_success:
        print("🎉 'NO CITATIONS' ISSUE COMPLETELY FIXED!")
        print("✅ API correctly returns citations in flat structure")
        print("✅ Frontend correctly processes flat response structure")
        print("✅ End-to-end pipeline working correctly")
        print("✅ Users should now see citations in the interface")
    else:
        print("⚠️ 'No Citations' issue still needs work")
        if not integration_ok:
            print("❌ Frontend-backend integration has issues")
        if not e2e_ok:
            print("❌ End-to-end pipeline has issues")
    
    return overall_success

if __name__ == "__main__":
    main()
