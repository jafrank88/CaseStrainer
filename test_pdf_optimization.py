#!/usr/bin/env python3
"""
Test script for PDF extraction optimization.
Demonstrates performance improvements over the current implementation.
"""

import os
import time
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_test_pdf():
    """Create a simple test PDF for benchmarking."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create temporary PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
        
        # Create PDF with test content
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "Test Document for PDF Extraction")
        c.drawString(100, 720, "This document contains legal citations:")
        c.drawString(100, 690, "Smith v. Jones, 123 U.S. 456 (2020)")
        c.drawString(100, 660, "Brown v. Board, 347 U.S. 483 (1954)")
        c.drawString(100, 630, "Roe v. Wade, 410 U.S. 113 (1973)")
        c.drawString(100, 600, "End of test document.")
        c.save()
        
        return pdf_path
    except ImportError:
        print("reportlab not available, using existing PDF if available")
        # Look for any existing PDF in the project
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith('.pdf'):
                    return os.path.join(root, file)
        return None

def benchmark_extraction_methods(pdf_path: str):
    """Benchmark different extraction methods."""
    print(f"\n=== PDF Extraction Benchmark ===")
    print(f"Testing file: {pdf_path}")
    print(f"File size: {os.path.getsize(pdf_path)} bytes")
    
    results = {}
    
    # Test 1: Current method (if available)
    try:
        from document_processing_unified import extract_text_from_file
        start_time = time.time()
        text = extract_text_from_file(pdf_path)
        current_time = time.time() - start_time
        results['current'] = {
            'time': current_time,
            'success': not text.startswith('Error:'),
            'text_length': len(text) if text else 0
        }
        print(f"✅ Current method: {current_time:.2f}s")
    except Exception as e:
        print(f"❌ Current method failed: {e}")
        results['current'] = {'time': 0, 'success': False, 'error': str(e)}
    
    # Test 2: Ultra-fast method
    try:
        from pdf_extraction_optimized import extract_text_from_pdf_ultra_fast
        start_time = time.time()
        text = extract_text_from_pdf_ultra_fast(pdf_path)
        ultra_fast_time = time.time() - start_time
        results['ultra_fast'] = {
            'time': ultra_fast_time,
            'success': not text.startswith('Error:'),
            'text_length': len(text) if text else 0
        }
        print(f"✅ Ultra-fast method: {ultra_fast_time:.2f}s")
    except Exception as e:
        print(f"❌ Ultra-fast method failed: {e}")
        results['ultra_fast'] = {'time': 0, 'success': False, 'error': str(e)}
    
    # Test 3: Smart method
    try:
        from pdf_extraction_optimized import extract_text_from_pdf_smart
        start_time = time.time()
        text = extract_text_from_pdf_smart(pdf_path)
        smart_time = time.time() - start_time
        results['smart'] = {
            'time': smart_time,
            'success': not text.startswith('Error:'),
            'text_length': len(text) if text else 0
        }
        print(f"✅ Smart method: {smart_time:.2f}s")
    except Exception as e:
        print(f"❌ Smart method failed: {e}")
        results['smart'] = {'time': 0, 'success': False, 'error': str(e)}
    
    return results

def print_benchmark_results(results: dict):
    """Print detailed benchmark results."""
    print(f"\n=== Benchmark Results ===")
    
    # Find the fastest successful method
    fastest_time = float('inf')
    fastest_method = None
    
    for method, result in results.items():
        if result['success'] and result['time'] < fastest_time:
            fastest_time = result['time']
            fastest_method = method
    
    for method, result in results.items():
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        time_str = f"{result['time']:.2f}s"
        
        if method == fastest_method:
            time_str += " 🏆 FASTEST"
        
        print(f"\n{method.upper()}:")
        print(f"  Status: {status}")
        print(f"  Time: {time_str}")
        print(f"  Text Length: {result.get('text_length', 0)}")
        
        if 'error' in result:
            print(f"  Error: {result['error']}")
    
    # Calculate improvements
    if 'current' in results and 'ultra_fast' in results:
        if results['current']['success'] and results['ultra_fast']['success']:
            current_time = results['current']['time']
            ultra_fast_time = results['ultra_fast']['time']
            
            if current_time > 0:
                improvement = ((current_time - ultra_fast_time) / current_time) * 100
                print(f"\n🚀 PERFORMANCE IMPROVEMENT:")
                print(f"  Ultra-fast is {improvement:.1f}% faster than current method")
                print(f"  Speedup: {current_time / ultra_fast_time:.1f}x")

def test_optimization_config():
    """Test the optimization configuration."""
    print(f"\n=== Optimization Configuration ===")
    
    try:
        from optimization_config import config, enable_optimized_mode, disable_optimized_mode
        
        print("Current settings:")
        summary = config.get_optimization_summary()
        for category, settings in summary.items():
            print(f"\n{category.upper()}:")
            for setting, value in settings.items():
                status = "✅ ENABLED" if value else "❌ DISABLED"
                print(f"  {setting}: {status}")
        
        print(f"\nOptimized Mode: {'✅ ENABLED' if config.is_optimized_mode() else '❌ DISABLED'}")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

def main():
    """Main test function."""
    print("=== PDF Extraction Optimization Test ===")
    
    # Test configuration
    test_optimization_config()
    
    # Create or find test PDF
    pdf_path = create_test_pdf()
    if not pdf_path:
        print("❌ No test PDF available")
        return
    
    print(f"\nUsing test PDF: {pdf_path}")
    
    # Run benchmarks
    results = benchmark_extraction_methods(pdf_path)
    
    # Print results
    print_benchmark_results(results)
    
    # Cleanup
    if pdf_path and 'tmp' in pdf_path:
        try:
            os.unlink(pdf_path)
            print(f"\nCleaned up temporary file: {pdf_path}")
        except:
            pass
    
    print(f"\n=== Test Complete ===")

if __name__ == "__main__":
    main() 