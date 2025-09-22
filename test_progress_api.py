#!/usr/bin/env python3

import requests
import json
import time

def test_progress_api():
    """Test API progress tracking."""
    
    # Simple text to trigger sync processing
    text = "The Supreme Court held in Spokeo, Inc. v. Robins, 136 S. Ct. 1540 (2016)."
    
    print("PROGRESS API TEST")
    print("=" * 50)
    print(f"Text: {text}")
    print()
    
    # Make API request
    url = "http://localhost:5000/casestrainer/api/analyze"
    data = {"text": text, "type": "text"}
    
    try:
        print("Making API request...")
        response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"Response received!")
            print(f"Success: {result.get('success', False)}")
            
            # Check progress data
            progress_data = result.get('progress_data', {})
            if progress_data:
                print("\nPROGRESS DATA:")
                print(f"  Status: {progress_data.get('status')}")
                print(f"  Overall Progress: {progress_data.get('overall_progress', 0)}%")
                print(f"  Elapsed Time: {progress_data.get('elapsed_time', 0):.2f}s")
                print(f"  Current Step: {progress_data.get('current_step', 0)}")
                print(f"  Current Message: {progress_data.get('current_message', 'N/A')}")
                
                steps = progress_data.get('steps', [])
                print(f"\nSTEPS ({len(steps)} total):")
                for i, step in enumerate(steps):
                    status_icon = "✅" if step['status'] == 'completed' else "🔄" if step['status'] == 'in_progress' else "⏳"
                    print(f"  {i}. {status_icon} {step['name']}: {step['progress']}% - {step['message']}")
            else:
                print("No progress data found in response")
            
            # Check citations
            citations = result.get('citations', [])
            print(f"\nFound {len(citations)} citations:")
            for i, citation in enumerate(citations[:3], 1):  # Show first 3
                print(f"  {i}. {citation.get('citation', 'N/A')} - {citation.get('case_name', 'N/A')}")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_progress_api()
