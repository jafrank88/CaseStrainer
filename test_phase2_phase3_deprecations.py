#!/usr/bin/env python3
"""
Test Phase 2 and Phase 3 deprecation warnings
"""

import sys
from pathlib import Path
import warnings

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

def test_enhanced_courtlistener_verifier_deprecation():
    """Test that EnhancedCourtListenerVerifier issues deprecation warning."""
    print("🧪 Testing EnhancedCourtListenerVerifier Deprecation")
    print("=" * 60)
    
    warnings_captured = []
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warnings_captured.append({
            'message': str(message),
            'category': category.__name__,
            'filename': filename,
            'lineno': lineno
        })
    
    # Capture warnings
    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler
    
    try:
        # Import and instantiate EnhancedCourtListenerVerifier
        from enhanced_courtlistener_verification import EnhancedCourtListenerVerifier
        
        # This should trigger a deprecation warning
        verifier = EnhancedCourtListenerVerifier("test_api_key")
        
        # Check if deprecation warning was issued
        deprecation_warnings = [w for w in warnings_captured if w['category'] == 'DeprecationWarning']
        
        print(f"✅ Warnings captured: {len(warnings_captured)}")
        print(f"✅ Deprecation warnings: {len(deprecation_warnings)}")
        
        if deprecation_warnings:
            for warning in deprecation_warnings:
                print(f"📋 Warning: {warning['message']}")
            print("🎉 SUCCESS: EnhancedCourtListenerVerifier properly issues deprecation warning!")
            return True
        else:
            print("❌ FAILURE: No deprecation warning issued")
            return False
            
    except Exception as e:
        print(f"❌ Error testing EnhancedCourtListenerVerifier: {e}")
        return False
    finally:
        warnings.showwarning = old_showwarning

def test_enhanced_fallback_verifier_deprecation():
    """Test that EnhancedFallbackVerifier issues deprecation warning."""
    print("\n🧪 Testing EnhancedFallbackVerifier Deprecation")
    print("=" * 60)
    
    warnings_captured = []
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warnings_captured.append({
            'message': str(message),
            'category': category.__name__,
            'filename': filename,
            'lineno': lineno
        })
    
    # Capture warnings
    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler
    
    try:
        # Import and instantiate EnhancedFallbackVerifier
        from enhanced_fallback_verifier import EnhancedFallbackVerifier
        
        # This should trigger a deprecation warning
        verifier = EnhancedFallbackVerifier()
        
        # Check if deprecation warning was issued
        deprecation_warnings = [w for w in warnings_captured if w['category'] == 'DeprecationWarning']
        
        print(f"✅ Warnings captured: {len(warnings_captured)}")
        print(f"✅ Deprecation warnings: {len(deprecation_warnings)}")
        
        if deprecation_warnings:
            for warning in deprecation_warnings:
                print(f"📋 Warning: {warning['message']}")
            print("🎉 SUCCESS: EnhancedFallbackVerifier properly issues deprecation warning!")
            return True
        else:
            print("❌ FAILURE: No deprecation warning issued")
            return False
            
    except Exception as e:
        print(f"❌ Error testing EnhancedFallbackVerifier: {e}")
        return False
    finally:
        warnings.showwarning = old_showwarning

def test_unified_sync_processor_deprecation():
    """Test that UnifiedSyncProcessor issues deprecation warning."""
    print("\n🧪 Testing UnifiedSyncProcessor Deprecation")
    print("=" * 60)
    
    warnings_captured = []
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warnings_captured.append({
            'message': str(message),
            'category': category.__name__,
            'filename': filename,
            'lineno': lineno
        })
    
    # Capture warnings
    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler
    
    try:
        # Import and instantiate UnifiedSyncProcessor
        from unified_sync_processor import UnifiedSyncProcessor
        
        # This should trigger a deprecation warning
        processor = UnifiedSyncProcessor()
        
        # Check if deprecation warning was issued
        deprecation_warnings = [w for w in warnings_captured if w['category'] == 'DeprecationWarning']
        
        print(f"✅ Warnings captured: {len(warnings_captured)}")
        print(f"✅ Deprecation warnings: {len(deprecation_warnings)}")
        
        if deprecation_warnings:
            for warning in deprecation_warnings:
                print(f"📋 Warning: {warning['message']}")
            print("🎉 SUCCESS: UnifiedSyncProcessor properly issues deprecation warning!")
            return True
        else:
            print("❌ FAILURE: No deprecation warning issued")
            return False
            
    except Exception as e:
        print(f"❌ Error testing UnifiedSyncProcessor: {e}")
        return False
    finally:
        warnings.showwarning = old_showwarning

def test_processing_options_still_works():
    """Test that ProcessingOptions still works (not deprecated yet)."""
    print("\n🧪 Testing ProcessingOptions (Should Still Work)")
    print("=" * 60)
    
    warnings_captured = []
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warnings_captured.append({
            'message': str(message),
            'category': category.__name__,
            'filename': filename,
            'lineno': lineno
        })
    
    # Capture warnings
    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler
    
    try:
        # Import and instantiate ProcessingOptions
        from unified_sync_processor import ProcessingOptions
        
        # This should NOT trigger a deprecation warning (yet)
        options = ProcessingOptions()
        
        # Check if any warnings were issued
        deprecation_warnings = [w for w in warnings_captured if w['category'] == 'DeprecationWarning']
        
        print(f"✅ Warnings captured: {len(warnings_captured)}")
        print(f"✅ Deprecation warnings: {len(deprecation_warnings)}")
        print(f"✅ ProcessingOptions created: {options is not None}")
        
        if len(deprecation_warnings) == 0:
            print("🎉 SUCCESS: ProcessingOptions does not issue deprecation warnings (as expected)!")
            return True
        else:
            print("❌ UNEXPECTED: ProcessingOptions issued deprecation warnings")
            for warning in deprecation_warnings:
                print(f"📋 Unexpected warning: {warning['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing ProcessingOptions: {e}")
        return False
    finally:
        warnings.showwarning = old_showwarning

def test_main_pipeline_still_works():
    """Test that the main pipeline still works without warnings."""
    print("\n🧪 Testing Main Pipeline (Should Work Without Warnings)")
    print("=" * 60)
    
    warnings_captured = []
    
    def warning_handler(message, category, filename, lineno, file=None, line=None):
        warnings_captured.append({
            'message': str(message),
            'category': category.__name__,
            'filename': filename,
            'lineno': lineno
        })
    
    # Capture warnings
    old_showwarning = warnings.showwarning
    warnings.showwarning = warning_handler
    
    try:
        # Import and use UnifiedCitationProcessorV2 (main pipeline)
        from unified_citation_processor_v2 import UnifiedCitationProcessorV2
        
        # This should NOT trigger any deprecation warnings
        processor = UnifiedCitationProcessorV2()
        
        # Check if any deprecation warnings were issued
        deprecation_warnings = [w for w in warnings_captured if w['category'] == 'DeprecationWarning']
        
        print(f"✅ Warnings captured: {len(warnings_captured)}")
        print(f"✅ Deprecation warnings: {len(deprecation_warnings)}")
        print(f"✅ Main processor created: {processor is not None}")
        
        if len(deprecation_warnings) == 0:
            print("🎉 SUCCESS: Main pipeline works without deprecation warnings!")
            return True
        else:
            print("❌ UNEXPECTED: Main pipeline issued deprecation warnings")
            for warning in deprecation_warnings:
                print(f"📋 Unexpected warning: {warning['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing main pipeline: {e}")
        return False
    finally:
        warnings.showwarning = old_showwarning

def main():
    print("🔍 Testing Phase 2 & 3 Deprecation Warnings")
    print("=" * 70)
    print("Verifying that Phase 2 and 3 components issue proper warnings")
    print("=" * 70)
    
    results = {
        'enhanced_courtlistener_verifier': test_enhanced_courtlistener_verifier_deprecation(),
        'enhanced_fallback_verifier': test_enhanced_fallback_verifier_deprecation(),
        'unified_sync_processor': test_unified_sync_processor_deprecation(),
        'processing_options_still_works': test_processing_options_still_works(),
        'main_pipeline_still_works': test_main_pipeline_still_works()
    }
    
    print(f"\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\n🎯 OVERALL RESULT: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 SUCCESS: All Phase 2 & 3 deprecation warnings are working properly!")
        print("✅ Phase 2 verification classes issue warnings")
        print("✅ Phase 3 UnifiedSyncProcessor issues warnings")
        print("✅ ProcessingOptions still works (not deprecated yet)")
        print("✅ Main pipeline works without warnings")
    else:
        print("⚠️ Some deprecation warnings need attention")
    
    print(f"\n💡 PHASE 2 & 3 BENEFITS:")
    print("• Enhanced verification classes properly deprecated")
    print("• UnifiedSyncProcessor deprecated due to architectural bypass")
    print("• ProcessingOptions preserved for gradual migration")
    print("• Main pipeline remains clean and functional")
    print("• Clear migration guidance provided to users")

if __name__ == "__main__":
    main()
