#!/usr/bin/env python3
"""
Test forcing immediate processing to bypass async queue
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from api.services.citation_service import CitationService

def main():
    local_path = r"D:\dev\casestrainer\D2 60382-9-II Published Opinion.pdf"
    
    print("=== Testing Force Immediate Processing ===")
    
    if not os.path.exists(local_path):
        print(f"Local file not found: {local_path}")
        return
    
    try:
        service = CitationService()
        
        # Test with force_mode to bypass async queue
        input_data = {
            'type': 'file', 
            'file_path': local_path, 
            'filename': os.path.basename(local_path),
            'file_size': os.path.getsize(local_path),
            'force_mode': 'sync'  # Force sync processing
        }
        
        print("Starting forced sync processing...")
        start_time = time.time()
        
        result = service.process_immediately(input_data)
        
        elapsed = time.time() - start_time
        print(f"Processing completed in {elapsed:.2f} seconds")
        
        if isinstance(result, dict):
            print(f"Success: {result.get('success')}")
            print(f"Error: {result.get('error')}")
            print(f"Citations found: {len(result.get('citations', []))}")
            print(f"Clusters found: {len(result.get('clusters', []))}")
            
            if result.get('success'):
                print("✅ Forced sync processing successful")
                if elapsed < 60:
                    print("🚀 Acceptable processing time")
                else:
                    print("⚠️ Still taking a long time, but completed successfully")
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
