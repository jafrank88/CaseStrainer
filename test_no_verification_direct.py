#!/usr/bin/env python3
"""
Test processing with verification completely disabled to check baseline performance
"""

import os
import sys
import time
import asyncio

sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from unified_citation_processor_v2 import UnifiedCitationProcessorV2

def main():
    local_path = r"D:\dev\casestrainer\D2 60382-9-II Published Opinion.pdf"
    
    print("=== Testing Processing Without Verification (Direct) ===")
    
    if not os.path.exists(local_path):
        print(f"Local file not found: {local_path}")
        return
    
    try:
        # Extract text first
        from robust_pdf_extractor import extract_text_from_pdf_smart
        print("Extracting text from PDF...")
        text = extract_text_from_pdf_smart(local_path)
        print(f"Extracted {len(text)} characters")
        
        # Process with verification disabled
        processor = UnifiedCitationProcessorV2()
        print("Starting citation processing...")
        start_time = time.time()
        
        # Run the async method
        result = asyncio.run(processor.process_text(text))
        
        elapsed = time.time() - start_time
        print(f"Processing completed in {elapsed:.2f} seconds")
        
        if isinstance(result, dict):
            print(f"Success: {result.get('success')}")
            print(f"Citations found: {len(result.get('citations', []))}")
            print(f"Clusters found: {len(result.get('clusters', []))}")
            
            if result.get('success'):
                print("✅ Processing successful")
                if elapsed < 30:
                    print("🚀 Fast processing!")
                else:
                    print(f"⚠️ Still taking {elapsed:.2f} seconds")
            else:
                print("❌ Processing failed")
        else:
            print(f"Unexpected result type: {type(result)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
