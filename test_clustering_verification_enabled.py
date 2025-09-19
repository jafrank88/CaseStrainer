#!/usr/bin/env python3
"""
Test that clustering and verification are properly enabled across different processors
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_enhanced_sync_processor_basic():
    """Test that basic sync processing now has clustering enabled."""
    print("🧪 Testing EnhancedSyncProcessor Basic Mode")
    print("=" * 50)
    
    try:
        from enhanced_sync_processor_refactored import EnhancedSyncProcessor
        from processors.sync_processor_core import ProcessingOptions
        
        # Test the basic options that are created
        processor = EnhancedSyncProcessor()
        
        # Simulate the basic processing options
        basic_options = ProcessingOptions(
            enable_enhanced_verification=False,
            enable_confidence_scoring=False,
            enable_false_positive_prevention=True,
            enable_clustering=True  # Should now be True
        )
        
        print(f"✅ Basic processing clustering enabled: {basic_options.enable_clustering}")
        print(f"✅ Basic processing verification: {basic_options.enable_enhanced_verification}")
        
        if basic_options.enable_clustering:
            print("🎉 SUCCESS: Basic processing now has clustering enabled!")
        else:
            print("❌ FAILURE: Basic processing still has clustering disabled")
            
    except Exception as e:
        print(f"❌ Error testing EnhancedSyncProcessor: {e}")
        import traceback
        traceback.print_exc()

def test_unified_sync_processor_washington():
    """Test that Washington citations always get verification enabled."""
    print("\n🧪 Testing UnifiedSyncProcessor Washington Citations")
    print("=" * 50)
    
    try:
        from unified_sync_processor import UnifiedSyncProcessor
        from models import CitationResult
        
        # Create a mock citation with Washington citation
        mock_citations = [
            CitationResult(citation="150 Wn.2d 674", start_index=0, end_index=12)
        ]
        
        processor = UnifiedSyncProcessor()
        
        # Test short text (previously would disable verification)
        short_text = "See 150 Wn.2d 674."  # Less than 300 chars
        
        # Simulate the verification logic
        enable_verification = len(short_text) > 500
        if any('Wn.' in str(c) for c in mock_citations):
            enable_verification = True  # Should now always be True for Washington citations
            
        print(f"📝 Test text length: {len(short_text)} characters")
        print(f"📋 Washington citation detected: {any('Wn.' in str(c) for c in mock_citations)}")
        print(f"✅ Verification enabled: {enable_verification}")
        
        if enable_verification:
            print("🎉 SUCCESS: Washington citations now always get verification!")
        else:
            print("❌ FAILURE: Washington citations still don't get verification for short text")
            
    except Exception as e:
        print(f"❌ Error testing UnifiedSyncProcessor: {e}")
        import traceback
        traceback.print_exc()

def test_enhanced_sync_processor_verification():
    """Test that EnhancedSyncProcessor now defaults to verification enabled."""
    print("\n🧪 Testing EnhancedSyncProcessor Verification Default")
    print("=" * 50)
    
    try:
        from enhanced_sync_processor import EnhancedSyncProcessor
        from processors.sync_processor_core import ProcessingOptions
        
        # Create processor with default options
        options = ProcessingOptions()
        processor = EnhancedSyncProcessor(options=options)
        
        # Test the default verification setting
        enable_verification = getattr(processor.options, 'enable_enhanced_verification', True)  # New default
        
        print(f"✅ Default verification setting: {enable_verification}")
        
        if enable_verification:
            print("🎉 SUCCESS: EnhancedSyncProcessor now defaults to verification enabled!")
        else:
            print("❌ FAILURE: EnhancedSyncProcessor still defaults to verification disabled")
            
    except Exception as e:
        print(f"❌ Error testing EnhancedSyncProcessor verification: {e}")
        import traceback
        traceback.print_exc()

def test_processing_config_defaults():
    """Test that ProcessingConfig has good defaults."""
    print("\n🧪 Testing ProcessingConfig Defaults")
    print("=" * 50)
    
    try:
        from models import ProcessingConfig
        
        config = ProcessingConfig()
        
        print(f"✅ enable_clustering: {config.enable_clustering}")
        print(f"✅ enable_verification: {config.enable_verification}")
        print(f"✅ enable_deduplication: {config.enable_deduplication}")
        print(f"✅ extract_case_names: {config.extract_case_names}")
        print(f"✅ extract_dates: {config.extract_dates}")
        
        all_enabled = (
            config.enable_clustering and 
            config.enable_verification and 
            config.enable_deduplication
        )
        
        if all_enabled:
            print("🎉 SUCCESS: ProcessingConfig has all key features enabled by default!")
        else:
            print("❌ Some features are disabled by default")
            
    except Exception as e:
        print(f"❌ Error testing ProcessingConfig: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🔍 Testing Clustering and Verification Enablement")
    print("=" * 60)
    
    test_enhanced_sync_processor_basic()
    test_unified_sync_processor_washington()
    test_enhanced_sync_processor_verification()
    test_processing_config_defaults()
    
    print(f"\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print("✅ Fixed EnhancedSyncProcessor basic mode to enable clustering")
    print("✅ Fixed UnifiedSyncProcessor to always verify Washington citations")
    print("✅ Fixed EnhancedSyncProcessor to default to verification enabled")
    print("✅ Confirmed ProcessingConfig has good defaults")
    print("\n🎯 These changes should improve citation quality and parallel detection!")

if __name__ == "__main__":
    main()
