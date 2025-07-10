#!/usr/bin/env python3
"""Quick test to see what extract_case_name_triple returns"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.case_name_extraction_core import extract_case_name_triple

def test_extract_function():
    """Test what extract_case_name_triple actually returns"""
    
    sample_text = 'Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions'
    citation = '200 Wn.2d 72, 73, 514 P.3d 643'
    
    print('Testing extract_case_name_triple:')
    print(f'Input text: {sample_text}')
    print(f'Citation: {citation}')
    print()
    
    try:
        result = extract_case_name_triple(
            text=sample_text, 
            citation=citation, 
            api_key=None, 
            context_window=200
        )
        
        print(f'Result type: {type(result)}')
        print(f'Result: {result}')
        
        if result:
            print(f'Keys: {list(result.keys())}')
            for key, value in result.items():
                print(f'  {key}: "{value}"')
        else:
            print('Result is None or empty')
            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    test_extract_function()
