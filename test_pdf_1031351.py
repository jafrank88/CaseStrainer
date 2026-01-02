#!/usr/bin/env python3
"""
Test the specific PDF 1031351.pdf to identify extraction vs processing issues
"""

import os
import sys
import time
import tempfile
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_pdf_extraction():
    """Test extraction of the specific PDF"""
    print("=" * 80)
    print("TESTING PDF 1031351.pdf - EXTRACTION vs PROCESSING")
    print("=" * 80)
    
    url = "https://www.courts.wa.gov/opinions/pdf/1031351.pdf"
    
    # Download PDF
    temp_file = download_pdf(url)
    if not temp_file:
        print("[ERROR] Failed to download PDF")
        return
        
    print(f"[INFO] PDF downloaded to: {temp_file}")
    print(f"[INFO] File size: {os.path.getsize(temp_file):,} bytes")
    
    # Test extraction with different libraries
    print("\n" + "-" * 60)
    print("TEST 1: RAW TEXT EXTRACTION")
    print("-" * 60)
    
    # Test PyMuPDF (fastest)
    print("\n[TEST] PyMuPDF (fitz) extraction:")
    try:
        import fitz
        start = time.time()
        doc = fitz.open(temp_file)
        text = ""
        for page_num in range(min(5, len(doc))):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
        doc.close()
        elapsed = time.time() - start
        print(f"[SUCCESS] Extracted {len(text):,} chars in {elapsed:.2f}s")
        print(f"[SAMPLE] First 500 chars:\n{text[:500]}")
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Test with CaseStrainer's robust extractor
    print("\n" + "-" * 60)
    print("TEST 2: CASESTRAINER ROBUST EXTRACTOR")
    print("-" * 60)
    
    try:
        from src.robust_pdf_extractor import extract_pdf_text_robust
        start = time.time()
        text, library = extract_pdf_text_robust(temp_file, max_pages=5, verbose=True)
        elapsed = time.time() - start
        print(f"[SUCCESS] Extracted {len(text):,} chars in {elapsed:.2f}s using {library}")
        print(f"[SAMPLE] First 500 chars:\n{text[:500]}")
        
        # Test citation extraction on this text
        print("\n" + "-" * 60)
        print("TEST 3: CITATION EXTRACTION FROM EXTRACTED TEXT")
        print("-" * 60)
        
        try:
            import asyncio
            from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2
            processor = UnifiedCitationProcessorV2()
            
            start = time.time()
            citations = asyncio.run(processor.process_text(text))
            elapsed = time.time() - start
            print(f"[SUCCESS] Found {len(citations)} citations in {elapsed:.2f}s")
            
            if citations:
                print(f"[SAMPLE] First 3 citations:")
                for i, cit in enumerate(citations[:3], 1):
                    print(f"  {i}. {cit.get('citation', 'N/A')}")
                    if cit.get('case_name'):
                        print(f"     Case: {cit['case_name']}")
        except Exception as e:
            print(f"[ERROR] Citation extraction failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"[ERROR] Robust extractor failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test full pipeline
    print("\n" + "-" * 60)
    print("TEST 4: FULL CASESTRAINER PIPELINE")
    print("-" * 60)
    
    try:
        from src.unified_input_processor import process_url_input
        import uuid
        
        request_id = str(uuid.uuid4())
        start = time.time()
        result = process_url_input(url, request_id)
        elapsed = time.time() - start
        print(f"[SUCCESS] Pipeline completed in {elapsed:.2f}s")
        print(f"[RESULT] Citations: {len(result.get('citations', []))}")
        print(f"[RESULT] Clusters: {len(result.get('clusters', []))}")
        
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test async worker path
    print("\n" + "-" * 60)
    print("TEST 5: ASYNC WORKER PATH (URL)")
    print("-" * 60)
    
    try:
        from src.unified_input_processor import UnifiedInputProcessor
        processor = UnifiedInputProcessor()
        
        # Test the decision logic for async processing
        input_data = {'url': url}
        start = time.time()
        should_be_async = processor._should_process_async(input_data, 'url')
        elapsed = time.time() - start
        print(f"[INFO] Async decision: {should_be_async} in {elapsed:.2f}s")
        
        # Test URL content detection
        print(f"[INFO] Testing URL content detection...")
        response = requests.head(url, timeout=10)
        content_type = response.headers.get('content-type', '')
        content_length = response.headers.get('content-length', '0')
        print(f"[INFO] Content-Type: {content_type}")
        print(f"[INFO] Content-Length: {content_length} bytes")
        
        # Test if it's a PDF
        is_pdf = 'pdf' in content_type.lower() or url.lower().endswith('.pdf')
        print(f"[INFO] Is PDF: {is_pdf}")
        
        # Check size threshold
        size_bytes = int(content_length) if content_length.isdigit() else 0
        size_kb = size_bytes / 1024
        print(f"[INFO] Size: {size_kb:.1f} KB")
        print(f"[INFO] Async threshold: 65 KB")
        print(f"[INFO] Will process async: {is_pdf and size_kb > 65}")
        
    except Exception as e:
        print(f"[ERROR] Async test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    try:
        os.unlink(temp_file)
    except:
        pass

def download_pdf(url: str) -> str:
    """Download PDF to temporary file"""
    try:
        print("[DOWNLOAD] Downloading PDF...")
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
            return f.name
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return None

if __name__ == "__main__":
    test_pdf_extraction()
