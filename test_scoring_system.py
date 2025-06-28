#!/usr/bin/env python3
"""
Test script for the new citation scoring system.
Tests various scenarios to ensure the scoring logic works correctly.
"""

import requests
import json
import time

def test_scoring_system():
    """Test the citation scoring system with various inputs."""
    
    # Test cases with different expected scores
    test_cases = [
        {
            "name": "Perfect citation with all data matching",
            "text": "In Smith v. Jones, 2023 U.S. 123, the court held that...",
            "expected_score": 4  # Should get 4 points: canonical name (2) + similarity (1) + year match (1)
        },
        {
            "name": "Citation with canonical name but no year match",
            "text": "The case of Brown v. State, 456 F.3d 789 (2022), established...",
            "expected_score": 3  # Should get 3 points: canonical name (2) + similarity (1)
        },
        {
            "name": "Citation with only extracted name",
            "text": "As stated in Johnson v. Doe, 789 S.W.2d 456...",
            "expected_score": 1  # Should get 1 point: similarity only
        },
        {
            "name": "Invalid citation format",
            "text": "Some random text without proper citation format",
            "expected_score": 0  # Should get 0 points: no verification data
        }
    ]
    
    print("Testing Citation Scoring System")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Input text: {test_case['text']}")
        print(f"Expected score: {test_case['expected_score']}/4")
        
        try:
            # Send request to the API
            response = requests.post(
                "http://localhost:5000/casestrainer/api/analyze",
                json={"text": test_case['text']},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if this is an async task
                if result.get('status') == 'processing' and result.get('task_id'):
                    task_id = result['task_id']
                    print(f"   ⏳ Async task started: {task_id}")
                    
                    # Wait for task completion
                    max_wait = 30  # seconds
                    wait_time = 0
                    while wait_time < max_wait:
                        time.sleep(2)
                        wait_time += 2
                        
                        # Check task status
                        status_response = requests.get(
                            f"http://localhost:5000/casestrainer/api/task/{task_id}",
                            timeout=10
                        )
                        
                        if status_response.status_code == 200:
                            status_result = status_response.json()
                            if status_result.get('status') == 'completed':
                                result = status_result
                                break
                            elif status_result.get('status') == 'failed':
                                print(f"   ❌ Task failed: {status_result.get('error', 'Unknown error')}")
                                break
                        else:
                            print(f"   ⚠️  Status check failed: {status_response.status_code}")
                    
                    if wait_time >= max_wait:
                        print(f"   ⏰ Task timeout after {max_wait} seconds")
                        continue
                
                citations = result.get('citations', [])
                
                if citations:
                    citation = citations[0]  # Get the first citation
                    score = citation.get('score', 0)
                    score_color = citation.get('scoreColor', 'red')
                    
                    print(f"✅ API Response:")
                    print(f"   Score: {score}/4 ({score_color})")
                    print(f"   Case Name: {citation.get('case_name', 'N/A')}")
                    print(f"   Extracted Case Name: {citation.get('extracted_case_name', 'N/A')}")
                    print(f"   Canonical Date: {citation.get('canonical_date', 'N/A')}")
                    print(f"   Extracted Date: {citation.get('extracted_date', 'N/A')}")
                    
                    # Check if score matches expectation
                    if score == test_case['expected_score']:
                        print(f"   ✅ Score matches expectation!")
                    else:
                        print(f"   ❌ Score mismatch! Expected {test_case['expected_score']}, got {score}")
                else:
                    print(f"   ⚠️  No citations found in response")
                    print(f"   Response: {result}")
            else:
                print(f"   ❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        print("-" * 50)
    
    print("\n" + "=" * 50)
    print("Scoring System Test Complete!")
    print("\nExpected Behavior:")
    print("• Score 4 (Green): Canonical name found (2) + name similarity (1) + year match (1)")
    print("• Score 3 (Green): Canonical name found (2) + name similarity (1)")
    print("• Score 2 (Yellow): Canonical name found (2) only")
    print("• Score 1 (Orange): Name similarity only")
    print("• Score 0 (Red): No verification data available")

if __name__ == "__main__":
    test_scoring_system() 