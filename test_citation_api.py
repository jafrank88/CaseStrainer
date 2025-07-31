"""Test script for the citation extraction API endpoint."""
import requests
import json

BASE_URL = "http://localhost:5000"  # Update if needed
ENDPOINT = f"{BASE_URL}/casestrainer/api/analyze/start"

test_cases = [
    {"text": "Brown v. Board of Education, 347 U.S. 483 (1954)", "expected": ["347 U.S. 483"]},
    {"text": "State v. Smith, 123 Wn.2d 456 (1993)", "expected": ["123 Wn.2d 456"]},
    {"text": "No citations here", "expected": []}
]

def test_citation_extraction():
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['text']}")
        try:
            # Start analysis
            response = requests.post(
                ENDPOINT,
                json={"text": test["text"], "document_type": "test"},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            task_id = response.json()["task_id"]
            
            # Get results (simplified - in real test, poll for completion)
            print(f"Started task: {task_id}")
            print("Note: Implement proper polling for results in a real test")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_citation_extraction()
