#!/usr/bin/env python3
"""
Test file processing directly to debug the stuck at 20% issue
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from api.services.citation_service import CitationService

def main():
    local_path = r"D:\dev\casestrainer\D2 60382-9-II Published Opinion.pdf"
    
    print("=== Testing File Processing ===")
    
    if not os.path.exists(local_path):
        print(f"Local file not found: {local_path}")
        return
    
    print(f"File exists: {local_path}")
    print(f"File size: {os.path.getsize(local_path)} bytes")
    
    try:
        service = CitationService()
        
        # Test the file extraction method that the API uses
        input_data = {
            'type': 'file', 
            'file_path': local_path, 
            'filename': os.path.basename(local_path),
            'file_size': os.path.getsize(local_path)
        }
        
        print("Starting file extraction...")
        start_time = time.time()
        
        result = service.extract_text_from_input(input_data)
        
        elapsed = time.time() - start_time
        print(f"Extraction completed in {elapsed:.2f} seconds")
        
        if isinstance(result, dict):
            print(f"Success: {result.get('success')}")
            print(f"Error: {result.get('error')}")
            text = result.get('text', '')
            print(f"Text length: {len(text)}")
            
            if len(text.strip()) > 0:
                print("✅ Text extraction successful")
                print(f"Preview: {text[:200]}...")
            else:
                print("❌ No text extracted")
        else:
            print(f"Unexpected result type: {type(result)}")
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
