#!/usr/bin/env python3
"""
Test to check what methods the enhanced_processor has
"""

from src.document_processing import enhanced_processor

def test_processor_methods():
    """Test what methods the enhanced_processor has"""
    
    print("🔍 Testing enhanced_processor methods...")
    print("-" * 60)
    
    # Check what methods the processor has
    methods = [method for method in dir(enhanced_processor) if not method.startswith('_')]
    print(f"Available methods: {methods}")
    
    # Check if it has process_text
    if hasattr(enhanced_processor, 'process_text'):
        print("✅ Has process_text method")
    else:
        print("❌ No process_text method")
    
    # Check if it has process_document
    if hasattr(enhanced_processor, 'process_document'):
        print("✅ Has process_document method")
    else:
        print("❌ No process_document method")
    
    # Check what type of processor it is
    print(f"Processor type: {type(enhanced_processor)}")
    print(f"Processor class: {enhanced_processor.__class__.__name__}")

if __name__ == "__main__":
    test_processor_methods() 