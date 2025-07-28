#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test to check citation extraction step by step.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test basic imports."""
    print("Testing imports...")
    try:
        from models import ProcessingConfig, CitationResult
        print("✅ models imported successfully")
        
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        print("✅ UnifiedCitationProcessorV2 imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test ProcessingConfig creation."""
    print("\nTesting ProcessingConfig...")
    try:
        from models import ProcessingConfig
        
        config = ProcessingConfig()
        print(f"✅ Default config created: debug_mode={config.debug_mode}")
        
        config = ProcessingConfig(debug_mode=True, enable_verification=False)
        print(f"✅ Custom config created: debug_mode={config.debug_mode}, verification={config.enable_verification}")
        
        return True
    except Exception as e:
        print(f"❌ Config creation failed: {e}")
        return False

def test_processor_init():
    """Test processor initialization."""
    print("\nTesting processor initialization...")
    try:
        from models import ProcessingConfig
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        # Try with minimal config first
        config = ProcessingConfig(debug_mode=False, enable_verification=False)
        processor = UnifiedCitationProcessorV2(config)
        print("✅ Processor initialized with minimal config")
        
        return True
    except Exception as e:
        print(f"❌ Processor initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_extraction():
    """Test simple citation extraction."""
    print("\nTesting simple citation extraction...")
    try:
        from models import ProcessingConfig
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        # Use minimal config to avoid hanging
        config = ProcessingConfig(
            debug_mode=False, 
            enable_verification=False,
            use_eyecite=False,  # Disable eyecite to avoid potential issues
            enable_clustering=False  # Disable clustering to simplify
        )
        processor = UnifiedCitationProcessorV2(config)
        
        # Very simple test text
        test_text = "See Brown v. Board, 347 U.S. 483 (1954)."
        print(f"Testing with: '{test_text}'")
        
        # Try the basic extraction method
        citations = processor.extract_citations_from_text(test_text)
        print(f"✅ Extraction completed, found {len(citations)} citations")
        
        if citations:
            for i, citation in enumerate(citations):
                print(f"  {i+1}. {citation.citation}")
        
        return len(citations) > 0
    except Exception as e:
        print(f"❌ Simple extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Simple Citation System Check")
    print("=" * 35)
    
    step1 = test_imports()
    if not step1:
        print("\n❌ Cannot proceed - import issues")
        exit(1)
    
    step2 = test_config()
    if not step2:
        print("\n❌ Cannot proceed - config issues")
        exit(1)
    
    step3 = test_processor_init()
    if not step3:
        print("\n❌ Cannot proceed - processor init issues")
        exit(1)
    
    step4 = test_simple_extraction()
    
    print("\n" + "=" * 35)
    print("SUMMARY:")
    print(f"Imports: {'✅' if step1 else '❌'}")
    print(f"Config: {'✅' if step2 else '❌'}")
    print(f"Processor Init: {'✅' if step3 else '❌'}")
    print(f"Simple Extraction: {'✅' if step4 else '❌'}")
    
    if all([step1, step2, step3, step4]):
        print("\n🎉 Basic citation system is working!")
    else:
        print("\n⚠️  Some issues detected with the citation system.")
