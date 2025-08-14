"""
Test script for citation processing functionality.
Run this script to verify that the process_citation_task_direct function works as expected.
"""

import sys
import os
import logging

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_citation_processing():
    """Test the citation processing functionality."""
    from src.progress_manager import process_citation_task_direct
    
    test_cases = [
        {
            "name": "Landmark Case Citation",
            "text": "This is a test citation to Brown v. Board of Education, 347 U.S. 483 (1954)."
        },
        {
            "name": "Multiple Citations",
            "text": "References to multiple cases: Roe v. Wade, 410 U.S. 113 (1973) and Miranda v. Arizona, 384 U.S. 436 (1966)."
        },
        {
            "name": "No Citations",
            "text": "This is just a regular text with no legal citations."
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"TEST {i}: {test_case['name']}")
        print(f"Input text: {test_case['text']}")
        print("-"*50)
        
        try:
            result = process_citation_task_direct(
                task_id=f"test_{i}",
                input_type="text",
                input_data={"text": test_case['text']}
            )
            
            print("Result:")
            print(f"- Status: {result.get('status', 'unknown')}")
            print(f"- Success: {result.get('success', False)}")
            
            if 'result' in result:
                print("\nExtracted Citations:")
                if isinstance(result['result'], dict) and 'citations' in result['result']:
                    for j, citation in enumerate(result['result']['citations'], 1):
                        print(f"  {j}. {citation.get('case_name', 'Unknown')} - {citation.get('citation', 'No citation')}")
                else:
                    print("  No citations found in the expected format.")
            
            if 'error' in result:
                print(f"\nError: {result['error']}")
                
        except Exception as e:
            print(f"Error during processing: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_citation_processing()
