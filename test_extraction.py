#!/usr/bin/env python3
"""Simple test to see what extract_case_name_triple returns and test verify_citation_with_extraction"""

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
            print('Result is None or False')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

def test_verify_function():
    """Test verify_citation_with_extraction directly"""
    print("\n" + "="*60)
    print("Testing verify_citation_with_extraction directly:")
    
    try:
        # Import the function from your app
        from src.app_final_vue import verify_citation_with_extraction
        
        sample_text = 'Convoyant, LLC v. DeepThink, LLC, 200 Wn.2d 72, 73, 514 P.3d 643 (2022). Certified questions'
        citation = '200 Wn.2d 72, 73, 514 P.3d 643'
        
        print(f'Input text: {sample_text}')
        print(f'Citation: {citation}')
        print()
        
        result = verify_citation_with_extraction(
            citation_text=citation,
            document_text=sample_text,
            api_key=None
        )
        
        print(f"verify_citation_with_extraction result:")
        print(f"  Type: {type(result)}")
        print(f"  extracted_case_name: '{result.get('extracted_case_name', 'MISSING')}'")
        print(f"  extracted_date: '{result.get('extracted_date', 'MISSING')}'")
        print(f"  canonical_name: '{result.get('canonical_name', 'MISSING')}'")
        print(f"  canonical_date: '{result.get('canonical_date', 'MISSING')}'")
        print(f"  verified: '{result.get('verified', 'MISSING')}'")
        print(f"  error: '{result.get('error', 'MISSING')}'")
        
        # Check if the mapping worked
        if result.get('extracted_case_name') == 'EXTRACTED_FAKE_NAME_Y':
            print("✅ SUCCESS: extracted_case_name mapped correctly!")
        else:
            print(f"❌ FAILED: extracted_case_name is '{result.get('extracted_case_name')}' instead of 'EXTRACTED_FAKE_NAME_Y'")
            
        if result.get('extracted_date') == '2099-12-31':
            print("✅ SUCCESS: extracted_date mapped correctly!")
        else:
            print(f"❌ FAILED: extracted_date is '{result.get('extracted_date')}' instead of '2099-12-31'")
            
    except Exception as e:
        print(f'Error testing verify_citation_with_extraction: {e}')
        import traceback
        traceback.print_exc()

def main():
    test_extract_function()
    test_verify_function()

if __name__ == "__main__":
    main() 