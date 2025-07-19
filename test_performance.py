#!/usr/bin/env python3
"""
Performance test for the optimized citation processor
"""

import time
from src.unified_citation_processor_v2 import UnifiedCitationProcessorV2, ProcessingConfig

def test_fast_processing():
    """Test fast processing without verification"""
    print("🚀 Testing Fast Processing (No Verification)")
    print("=" * 50)
    
    # Test text with citations
    test_text = "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
    
    # Fast config (no verification)
    fast_config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=False,  # No verification for speed
        debug_mode=False,
        min_confidence=0.0
    )
    
    processor = UnifiedCitationProcessorV2(fast_config)
    
    start_time = time.time()
    results = processor.process_text(test_text)
    processing_time = time.time() - start_time
    
    print(f"⏱️  Processing time: {processing_time:.2f} seconds")
    print(f"📚 Found {len(results)} citations")
    
    for i, result in enumerate(results, 1):
        print(f"  {i}. Citation: {result.citation}")
        print(f"     Extracted case name: {result.extracted_case_name}")
        print(f"     Extracted date: {result.extracted_date}")
        print(f"     Verified: {result.verified}")
        print()
    
    return processing_time < 5.0  # Should be under 5 seconds

def test_full_processing():
    """Test full processing with verification"""
    print("🔍 Testing Full Processing (With Verification)")
    print("=" * 50)
    
    # Test text with citations
    test_text = "In Smith v. Jones, 123 F.3d 456 (2d Cir. 1995), the court held that..."
    
    # Full config (with verification)
    full_config = ProcessingConfig(
        use_eyecite=True,
        use_regex=True,
        extract_case_names=True,
        extract_dates=True,
        enable_clustering=True,
        enable_deduplication=True,
        enable_verification=True,  # With verification
        debug_mode=False,
        min_confidence=0.0
    )
    
    processor = UnifiedCitationProcessorV2(full_config)
    
    start_time = time.time()
    results = processor.process_text(test_text)
    processing_time = time.time() - start_time
    
    print(f"⏱️  Processing time: {processing_time:.2f} seconds")
    print(f"📚 Found {len(results)} citations")
    
    for i, result in enumerate(results, 1):
        print(f"  {i}. Citation: {result.citation}")
        print(f"     Extracted case name: {result.extracted_case_name}")
        print(f"     Extracted date: {result.extracted_date}")
        print(f"     Verified: {result.verified}")
        print(f"     Source: {result.source}")
        print()
    
    return processing_time < 30.0  # Should be under 30 seconds

def main():
    """Run performance tests"""
    print("🧪 Performance Tests")
    print("=" * 60)
    
    # Test fast processing
    fast_success = test_fast_processing()
    print()
    
    # Test full processing
    full_success = test_full_processing()
    print()
    
    # Summary
    print("📊 Performance Test Results")
    print("=" * 30)
    print(f"Fast processing: {'✅ PASS' if fast_success else '❌ FAIL'}")
    print(f"Full processing: {'✅ PASS' if full_success else '❌ FAIL'}")
    
    if fast_success and full_success:
        print("\n🎉 All performance tests passed!")
    else:
        print("\n⚠️  Some performance tests failed. Consider further optimization.")

if __name__ == "__main__":
    main() 