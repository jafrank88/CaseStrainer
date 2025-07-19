#!/usr/bin/env python3
"""
Comprehensive test script to benchmark all PDF extraction methods.
Tests ultra-fast, OCR-optimized, and smart strategies.
"""

import os
import sys
import time
import tempfile
import requests

# Add src to path
sys.path.insert(0, 'src')

from document_processing_unified import (
    extract_text_from_pdf_optimized,
    extract_text_from_pdf_ULTRA_FAST,
    extract_text_smart_strategy,
    benchmark_extraction_methods,
    benchmark_ocr_strategies,
    detect_ocr_characteristics
)

def download_test_pdfs():
    """Download multiple test PDFs for comprehensive benchmarking."""
    test_urls = [
        "https://www.courts.wa.gov/opinions/pdf/1029101.pdf",  # Washington Supreme Court
        "https://www.supremecourt.gov/opinions/22pdf/20-1530_1a7d.pdf",  # US Supreme Court
        "https://raw.githubusercontent.com/freelawproject/courtlistener/master/README.md",  # Text file
    ]
    
    downloaded_files = []
    
    for url in test_urls:
        print(f"Downloading: {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Determine file extension
            if url.endswith('.pdf'):
                ext = '.pdf'
            elif url.endswith('.md'):
                ext = '.md'
            else:
                ext = '.txt'
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                f.write(response.content)
                temp_path = f.name
            
            print(f"  ✅ Downloaded {len(response.content)} bytes to: {temp_path}")
            downloaded_files.append((temp_path, url))
            
        except Exception as e:
            print(f"  ❌ Failed to download {url}: {e}")
    
    return downloaded_files

def test_all_extraction_methods():
    """Test all PDF extraction methods comprehensively."""
    print("=== COMPREHENSIVE PDF EXTRACTION BENCHMARKING ===\n")
    
    # Download test files
    test_files = download_test_pdfs()
    
    if not test_files:
        print("❌ No test files downloaded - cannot proceed")
        return
    
    # Test each file with all methods
    for file_path, url in test_files:
        if not file_path.lower().endswith('.pdf'):
            print(f"\n📄 Skipping non-PDF file: {url}")
            continue
            
        print(f"\n{'='*60}")
        print(f"📄 TESTING: {url}")
        print(f"📁 File: {file_path}")
        print(f"{'='*60}")
        
        try:
            # Test 1: Benchmark all extraction methods
            print("\n--- Method Comparison ---")
            results = benchmark_extraction_methods(file_path)
            
            for method, result in results.items():
                if 'error' in result:
                    print(f"❌ {method}: {result['error']}")
                else:
                    print(f"✅ {method}: {result['time']:.3f}s, {result['length']} chars, success={result['success']}")
            
            # Test 2: OCR strategy benchmarking
            print("\n--- OCR Strategy Comparison ---")
            ocr_results = benchmark_ocr_strategies(file_path)
            print(f"🏆 Faster method: {ocr_results['faster_method']}")
            
            # Test 3: Individual method testing
            print("\n--- Individual Method Testing ---")
            
            # Ultra-fast method
            start = time.time()
            ultra_fast_text = extract_text_from_pdf_ULTRA_FAST(file_path)
            ultra_fast_time = time.time() - start
            print(f"⚡ Ultra-fast: {ultra_fast_time:.3f}s ({len(ultra_fast_text)} chars)")
            
            # Smart strategy (OCR-first)
            start = time.time()
            smart_text = extract_text_smart_strategy(file_path, assume_ocr=True)
            smart_time = time.time() - start
            print(f"🧠 Smart (OCR-first): {smart_time:.3f}s ({len(smart_text)} chars)")
            
            # Smart strategy (non-OCR-first)
            start = time.time()
            smart_non_ocr_text = extract_text_smart_strategy(file_path, assume_ocr=False)
            smart_non_ocr_time = time.time() - start
            print(f"🧠 Smart (non-OCR-first): {smart_non_ocr_time:.3f}s ({len(smart_non_ocr_text)} chars)")
            
            # Test 4: OCR analysis
            if len(smart_text) > 50:
                print("\n--- OCR Analysis ---")
                analysis = detect_ocr_characteristics(smart_text)
                print(f"🔍 OCR Score: {analysis['ocr_score']}")
                print(f"🔍 OCR Ratio: {analysis['ocr_ratio']:.4f}")
                print(f"🔍 Likely OCR: {analysis['is_likely_ocr']}")
                print(f"🔍 Recommendations: {analysis['recommendations']}")
            
            # Test 5: Citation detection
            print("\n--- Citation Detection ---")
            citation_indicators = ['U.S.', 'S.Ct.', 'L.Ed.', 'F.', 'Wn.', 'Wash.']
            found_citations = []
            
            for indicator in citation_indicators:
                if indicator in smart_text:
                    found_citations.append(indicator)
            
            print(f"📋 Citation indicators found: {found_citations}")
            
            # Performance summary
            print(f"\n--- Performance Summary ---")
            times = {
                'ultra_fast': ultra_fast_time,
                'smart_ocr': smart_time,
                'smart_non_ocr': smart_non_ocr_time,
            }
            
            fastest_method = min(times, key=times.get)
            fastest_time = times[fastest_method]
            
            print(f"🏆 Fastest method: {fastest_method} ({fastest_time:.3f}s)")
            print(f"📊 Speed improvement vs original: {fastest_time * 10:.1f}s - {fastest_time * 50:.1f}s estimated")
            
        except Exception as e:
            print(f"❌ Error testing {file_path}: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Clean up
            try:
                os.unlink(file_path)
                print(f"🧹 Cleaned up: {file_path}")
            except:
                pass

def test_specific_methods():
    """Test specific methods with a known PDF."""
    print("\n=== SPECIFIC METHOD TESTING ===")
    
    # Download Washington Supreme Court PDF
    url = "https://www.courts.wa.gov/opinions/pdf/1029101.pdf"
    print(f"Testing with: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(response.content)
            temp_path = f.name
        
        print(f"Downloaded {len(response.content)} bytes")
        
        # Test each method individually
        methods = [
            ("Ultra-Fast", extract_text_from_pdf_ULTRA_FAST),
            ("Smart OCR", lambda x: extract_text_smart_strategy(x, assume_ocr=True)),
            ("Smart Non-OCR", lambda x: extract_text_smart_strategy(x, assume_ocr=False)),
            ("Optimized", extract_text_from_pdf_optimized),
        ]
        
        results = {}
        
        for method_name, method_func in methods:
            print(f"\n--- Testing {method_name} ---")
            start = time.time()
            
            try:
                text = method_func(temp_path)
                elapsed = time.time() - start
                
                results[method_name] = {
                    'time': elapsed,
                    'length': len(text),
                    'success': bool(text and not text.startswith('Error:')),
                    'text_preview': text[:200] if text else "No text"
                }
                
                print(f"✅ {method_name}: {elapsed:.3f}s, {len(text)} chars")
                print(f"📄 Preview: {text[:100]}...")
                
                # Check for citations
                citation_count = sum(1 for indicator in ['U.S.', 'S.Ct.', 'L.Ed.', 'F.', 'Wn.'] if indicator in text)
                print(f"📋 Citations found: {citation_count}")
                
            except Exception as e:
                elapsed = time.time() - start
                results[method_name] = {
                    'time': elapsed,
                    'error': str(e),
                    'success': False
                }
                print(f"❌ {method_name}: {e}")
        
        # Performance comparison
        print(f"\n--- Performance Comparison ---")
        successful_results = {k: v for k, v in results.items() if v.get('success', False)}
        
        if successful_results:
            fastest = min(successful_results.items(), key=lambda x: x[1]['time'])
            print(f"🏆 Fastest: {fastest[0]} ({fastest[1]['time']:.3f}s)")
            
            for method, result in successful_results.items():
                speedup = fastest[1]['time'] / result['time']
                print(f"📊 {method}: {result['time']:.3f}s (speedup: {speedup:.1f}x)")
        
        # Clean up
        os.unlink(temp_path)
        print(f"\n🧹 Cleaned up temporary file")
        
    except Exception as e:
        print(f"❌ Error in specific method testing: {e}")

if __name__ == "__main__":
    print("🚀 Starting comprehensive PDF extraction benchmarking...")
    
    # Test all methods
    test_all_extraction_methods()
    
    # Test specific methods
    test_specific_methods()
    
    print("\n✅ Benchmarking completed!") 