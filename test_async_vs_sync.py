#!/usr/bin/env python3
"""
Test if the issue is with async vs sync processing
"""

import sys
from pathlib import Path
import re
import os

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_text_vs_file_processing():
    """Test text processing vs file processing to isolate the issue."""
    
    print("🔍 Testing Text vs File Processing")
    print("=" * 50)
    
    # Extract text from PDF
    pdf_path = r"D:\dev\casestrainer\gov.uscourts.wyd.64014.141.0_1.pdf"
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
        doc.close()
        
        print(f"📄 Extracted {len(text)} characters from PDF")
        
        # Test 1: Direct text processing with UnifiedSyncProcessor
        print("\n🧪 Test 1: Direct text processing")
        try:
            from unified_sync_processor import UnifiedSyncProcessor
            
            processor = UnifiedSyncProcessor()
            result = processor.process_text_unified(text)
            
            citations = result.get('citations', [])
            wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
            
            print(f"  Total citations: {len(citations)}")
            print(f"  WL citations: {len(wl_citations)}")
            
            if wl_citations:
                print("  ✅ Direct text processing found WL citations:")
                for citation in wl_citations[:5]:  # Show first 5
                    print(f"    - {citation.get('citation')}")
                if len(wl_citations) > 5:
                    print(f"    ... and {len(wl_citations) - 5} more")
            else:
                print("  ❌ Direct text processing found no WL citations")
                
        except Exception as e:
            print(f"  ❌ Error in direct text processing: {e}")
        
        # Test 2: API text processing
        print("\n🧪 Test 2: API text processing")
        try:
            import requests
            
            # Use a smaller sample of text to ensure sync processing
            sample_text = text[:2000]  # First 2KB to ensure sync processing
            
            response = requests.post('http://localhost:5000/casestrainer/api/analyze', 
                                   data={'text': sample_text, 'type': 'text'}, 
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                citations = result.get('citations', [])
                wl_citations = [c for c in citations if 'WL' in c.get('citation', '')]
                
                print(f"  ✅ API text processing: {len(citations)} total, {len(wl_citations)} WL citations")
                
                if wl_citations:
                    for citation in wl_citations:
                        print(f"    - {citation.get('citation')}")
                else:
                    print("  ❌ API text processing found no WL citations")
            else:
                print(f"  ❌ API text error: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error in API text processing: {e}")
        
        # Test 3: Check if file size triggers async processing
        print(f"\n🧪 Test 3: File size analysis")
        print(f"  PDF file size: {os.path.getsize(pdf_path)} bytes")
        print(f"  Extracted text size: {len(text)} bytes")
        
        # Check thresholds
        try:
            from unified_sync_processor import ProcessingOptions
            options = ProcessingOptions()
            print(f"  Sync threshold: {options.sync_threshold} bytes")
            
            if len(text) > options.sync_threshold:
                print(f"  ⚠️  Text size exceeds sync threshold - will use async processing")
                print(f"     This might explain why file upload returns 0 citations")
            else:
                print(f"  ✅ Text size within sync threshold")
                
        except Exception as e:
            print(f"  ❌ Error checking thresholds: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    test_text_vs_file_processing()
    
    print(f"\n" + "=" * 50)
    print("📋 DIAGNOSIS:")
    print("=" * 50)
    print("If direct text processing finds WL citations but file upload doesn't:")
    print("  → Issue is in file processing pipeline or async processing")
    print("If API text processing works but file upload doesn't:")
    print("  → Issue is specifically with file upload handling")
    print("If text size exceeds sync threshold:")
    print("  → File is being processed async, need to check async pipeline")

if __name__ == "__main__":
    main()
