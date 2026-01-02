#!/usr/bin/env python3
"""
Test what processing mode is being determined for this file
"""

import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from api.services.citation_service import CitationService

def main():
    local_path = r"D:\dev\casestrainer\D2 60382-9-II Published Opinion.pdf"
    
    print("=== Testing Processing Mode Determination ===")
    
    if not os.path.exists(local_path):
        print(f"Local file not found: {local_path}")
        return
    
    try:
        service = CitationService()
        
        # Test input data
        input_data = {
            'type': 'file', 
            'file_path': local_path, 
            'filename': os.path.basename(local_path),
            'file_size': os.path.getsize(local_path)
        }
        
        print(f"File size: {input_data['file_size']} bytes")
        print(f"File size in KB: {input_data['file_size'] / 1024:.2f} KB")
        
        # Check what processing mode would be used
        should_immediate = service.should_process_immediately(input_data)
        print(f"Should process immediately: {should_immediate}")
        
        # Check processing mode
        processing_mode = service.determine_processing_mode(input_data)
        print(f"Determined processing mode: {processing_mode}")
        
        # Test the text extraction first
        print("\n=== Testing Text Extraction ===")
        text_result = service.extract_text_from_input(input_data)
        
        if isinstance(text_result, dict):
            text = text_result.get('text', '')
            print(f"Text extraction success: {text_result.get('success')}")
            print(f"Extracted text length: {len(text)} characters")
            
            if len(text) > 0:
                # Now test processing mode based on text
                text_input = {'type': 'text', 'text': text}
                text_mode = service.determine_processing_mode(text_input)
                print(f"Processing mode for extracted text: {text_mode}")
                
                should_immediate_text = service.should_process_immediately(text_input)
                print(f"Should process text immediately: {should_immediate_text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
