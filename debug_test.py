#!/usr/bin/env python3
"""Very simple debug test"""

print("Starting debug test...")

try:
    print("Step 1: Importing extract_case_name_triple")
    import sys
    sys.path.insert(0, 'src')
    from case_name_extraction_core import extract_case_name_triple
    
    print("Step 2: Testing extract_case_name_triple")
    result = extract_case_name_triple("test", "test")
    print(f"Result: {result}")
    print(f"Type: {type(result)}")
    
    if result:
        print(f"Keys: {list(result.keys())}")
        print(f"extracted_name: {result.get('extracted_name')}")
        print(f"extracted_date: {result.get('extracted_date')}")
    
    print("✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 