#!/usr/bin/env python3
"""
Backend API Test Script
Test the citation extraction pipeline via direct API calls to verify functionality
"""

import requests
import json
import time
import sys

# API endpoint
BASE_URL = "https://wolf.law.uw.edu/casestrainer/api"
ANALYZE_URL = f"{BASE_URL}/analyze"
TASK_STATUS_URL = f"{BASE_URL}/task_status"

def test_text_analysis():
    """Test text analysis via API"""
    print("=" * 60)
    print("TESTING TEXT ANALYSIS VIA API")
    print("=" * 60)
    
    # Test cases with known citations
    test_cases = [
        {
            'name': 'Simple Citation',
            'text': 'Brown v. Board of Education, 347 U.S. 483 (1954)',
            'expected_citations': 1
        },
        {
            'name': 'Multiple Citations',
            'text': 'The Supreme Court decided in Brown v. Board of Education, 347 U.S. 483 (1954), that separate educational facilities are inherently unequal. This landmark case overturned Plessy v. Ferguson, 163 U.S. 537 (1896). Another important case is Miranda v. Arizona, 384 U.S. 436 (1966), which established the Miranda rights.',
            'expected_citations': 3
        },
        {
            'name': 'Federal Circuit Citation',
            'text': 'The court ruled in Smith v. Jones, 123 F.3d 456 (9th Cir. 2020).',
            'expected_citations': 1
        },
        {
            'name': 'State Court Citation',
            'text': 'In Johnson v. State, 789 P.2d 123 (Wash. 2019), the court held...',
            'expected_citations': 1
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        print(f"Text: {test_case['text'][:100]}{'...' if len(test_case['text']) > 100 else ''}")
        print(f"Expected Citations: {test_case['expected_citations']}")
        
        # Prepare request payload
        payload = {
            'text': test_case['text'],
            'type': 'text'
        }
        
        try:
            # Send request to API
            print("Sending request to API...")
            response = requests.post(
                ANALYZE_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
                
                # Check if it's an async task
                if 'task_id' in result:
                    task_id = result['task_id']
                    print(f"Task ID: {task_id}")
                    print("Polling for results...")
                    
                    # Poll for results
                    final_result = poll_for_results(task_id)
                    if final_result:
                        analyze_results(final_result, test_case)
                    else:
                        print("❌ Failed to get results from task")
                        
                elif 'citations' in result:
                    # Immediate result
                    analyze_results(result, test_case)
                else:
                    print(f"❌ Unexpected response format: {result}")
                    
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

def poll_for_results(task_id, max_attempts=10, delay=3):
    """Poll for task results"""
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{TASK_STATUS_URL}/{task_id}", timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                
                print(f"Attempt {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    return result.get('result', result)
                elif status == 'failed':
                    print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
                    return None
                elif status in ['processing', 'pending']:
                    print(f"Task still {status}, waiting {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"Unknown status: {status}")
                    
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Status check error: {e}")
            
    print("❌ Task polling timed out")
    return None

def analyze_results(result, test_case):
    """Analyze the API results"""
    citations = result.get('citations', [])
    clusters = result.get('clusters', [])
    
    print(f"Citations Found: {len(citations)}")
    print(f"Clusters Found: {len(clusters)}")
    
    # Check if we got the expected number of citations
    expected = test_case['expected_citations']
    actual = len(citations)
    
    if actual >= expected:
        print(f"✅ Citation count: Expected ≥{expected}, Got {actual}")
    else:
        print(f"❌ Citation count: Expected ≥{expected}, Got {actual}")
    
    # Display first few citations
    for i, citation in enumerate(citations[:3]):  # Show first 3
        print(f"\nCitation {i+1}:")
        if isinstance(citation, dict):
            print(f"  Citation: {citation.get('citation', 'N/A')}")
            print(f"  Case Name: {citation.get('extracted_case_name', 'N/A')}")
            print(f"  Year: {citation.get('extracted_date', 'N/A')}")
            print(f"  Verified: {citation.get('verified', 'N/A')}")
        else:
            print(f"  Raw: {citation}")
    
    # Display clusters
    if clusters:
        print(f"\nClusters:")
        for i, cluster in enumerate(clusters[:2]):  # Show first 2
            print(f"  Cluster {i+1}: {len(cluster.get('citations', []))} citations")

def test_health_endpoint():
    """Test the health endpoint"""
    print("\n" + "=" * 60)
    print("TESTING HEALTH ENDPOINT")
    print("=" * 60)
    
    health_url = f"{BASE_URL}/health"
    
    try:
        response = requests.get(health_url, timeout=10)
        print(f"Health Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health check passed: {result}")
        else:
            print(f"❌ Health check failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")

def main():
    """Main test function"""
    print("BACKEND API CITATION EXTRACTION TEST")
    print("Testing citation extraction pipeline via direct API calls")
    print(f"Base URL: {BASE_URL}")
    
    # Test health endpoint first
    test_health_endpoint()
    
    # Test text analysis
    test_text_analysis()
    
    print("\n" + "=" * 60)
    print("BACKEND API TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
